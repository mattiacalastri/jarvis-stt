#!/usr/local/bin/python3.10
"""
Voice Briefing — generate TTS audio via ElevenLabs + send to Telegram as voice message.

Shared core for:
  - /garden-walk (briefing mattutino)
  - /session-end (briefing fine sessione)
  - Any skill/hook/cron that needs to speak to Mattia

Usage:
    python3 voice_briefing.py "testo da parlare" [--chat $OWNER_CHAT_ID] [--save path.mp3]
    echo "testo" | python3 voice_briefing.py - [--save path.mp3]

Configuration (env vars):
    OWNER_CHAT_ID     Telegram chat_id authorized to receive voice messages.
                      Required. The bot is hard-locked to this single chat.
    ELEVENLABS_API_KEY  In ~/claude_voice/.env

Exit 0 on success. Exit 1 on TTS/TG failure.
"""

import os
import sys
import ssl
import json
import argparse
import subprocess
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

import certifi


OWNER_CHAT_ID = os.environ.get("OWNER_CHAT_ID", "").strip()
if not OWNER_CHAT_ID:
    # Fallback: leggi da ~/claude_voice/.env se OWNER_CHAT_ID è definito lì
    _env_owner = (Path.home() / "claude_voice" / ".env")
    if _env_owner.exists():
        for _line in _env_owner.read_text().splitlines():
            if _line.startswith("OWNER_CHAT_ID="):
                OWNER_CHAT_ID = _line.split("=", 1)[1].strip().strip('"').strip("'")
                break
if not OWNER_CHAT_ID:
    raise RuntimeError(
        "OWNER_CHAT_ID not configured. Set the env var or add OWNER_CHAT_ID=<your_telegram_chat_id> "
        "to ~/claude_voice/.env (the chat_id authorized to receive voice briefings)."
    )
ASTRA_ENV = Path.home() / "claude_voice" / ".env"
POLPO_BOTS_ENV = Path.home() / ".config" / "credentials" / "polpo_bots.env"

# Audio Jarvis notifications isolate su bot dedicato polpo_jarvis_bot
# per uscire dalla cascata di notifiche di astra_os_bot.
# Priority: POLPO_JARVIS_BOT_TOKEN (polpo_bots.env o claude_voice/.env) > ASTRA_TG_BOT_TOKEN fallback.

ELEVEN_VOICE_ID = "DLMxnwJE0a28JQLTMJPJ"
ELEVEN_MODEL = "eleven_turbo_v2_5"
VOICE_SETTINGS = {
    "stability": 0.35,
    "similarity_boost": 0.85,
    "style": 0.55,
    "use_speaker_boost": True,
    "speed": 1.2,  # ElevenLabs hard cap — Mattia prefers max speed (sess.854)
}


def _load_env_var(env_file: Path, key: str) -> str | None:
    if not env_file.exists():
        return None
    for line in env_file.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def synthesize(text: str) -> bytes:
    api_key = _load_env_var(ASTRA_ENV, "ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError(f"ELEVENLABS_API_KEY not found in {ASTRA_ENV}")

    ctx = ssl.create_default_context(cafile=certifi.where())
    payload = json.dumps({
        "text": text,
        "model_id": ELEVEN_MODEL,
        "voice_settings": VOICE_SETTINGS,
    }).encode()

    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}",
        data=payload,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        return r.read()


def _resolve_voice_bot_token() -> tuple[str, str]:
    """Prefer dedicated Jarvis voice bot, fallback to astra_os_bot.
    Returns (token, source_label) for debug visibility."""
    for env_file in (POLPO_BOTS_ENV, ASTRA_ENV):
        token = _load_env_var(env_file, "POLPO_JARVIS_BOT_TOKEN")
        if token:
            return token, f"POLPO_JARVIS_BOT_TOKEN@{env_file.name}"
    token = _load_env_var(ASTRA_ENV, "ASTRA_TG_BOT_TOKEN")
    if token:
        return token, "ASTRA_TG_BOT_TOKEN@.env (fallback)"
    raise RuntimeError(
        f"Neither POLPO_JARVIS_BOT_TOKEN nor ASTRA_TG_BOT_TOKEN found in {POLPO_BOTS_ENV} or {ASTRA_ENV}"
    )


def send_voice(audio_bytes: bytes, chat_id: str, caption: str = "") -> None:
    # HARD LOCK: il bot Jarvis spedisce SOLO al chat_id configurato in OWNER_CHAT_ID.
    # Come gli altri bot single-owner (Falco, Flexa), Jarvis è locked per design.
    if str(chat_id) != OWNER_CHAT_ID:
        raise RuntimeError(
            f"SECURITY LOCK: voice_briefing can only send to OWNER_CHAT_ID={OWNER_CHAT_ID}, "
            f"refused chat_id={chat_id}"
        )
    token, source = _resolve_voice_bot_token()

    ctx = ssl.create_default_context(cafile=certifi.where())
    boundary = "----voicebriefing" + os.urandom(8).hex()
    body = []
    body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat_id}\r\n".encode())
    if caption:
        body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n".encode())
    body.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"voice\"; filename=\"briefing.mp3\"\r\n"
        f"Content-Type: audio/mpeg\r\n\r\n".encode()
    )
    body.append(audio_bytes)
    body.append(f"\r\n--{boundary}--\r\n".encode())
    data = b"".join(body)

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendVoice",
        data=data,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        resp = json.loads(r.read())
        if not resp.get("ok"):
            raise RuntimeError(f"Telegram error: {resp}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Voice briefing to Telegram")
    parser.add_argument("text", help="Text to speak, or '-' to read from stdin")
    parser.add_argument("--chat", default=OWNER_CHAT_ID, help="Telegram chat ID")
    parser.add_argument("--caption", default="", help="Optional text caption under voice")
    parser.add_argument("--save", help="Save MP3 to this path (optional)")
    parser.add_argument("--no-send", action="store_true", help="Skip Telegram send")
    parser.add_argument("--play", action="store_true", help="Play audio locally on Mac via afplay")
    args = parser.parse_args()

    text = sys.stdin.read() if args.text == "-" else args.text
    text = text.strip()
    # Jarvis always addresses Mattia as "Signore" — prepend if not already present
    if text and not text.lower().startswith("signore"):
        text = "Signore, " + text
    if not text:
        print("empty text", file=sys.stderr)
        return 1

    try:
        audio = synthesize(text)
    except Exception as e:
        print(f"TTS failed: {e}", file=sys.stderr)
        return 1

    if args.save:
        Path(args.save).expanduser().write_bytes(audio)
        print(f"saved: {args.save} ({len(audio)} byte)")

    if args.play:
        # Use save path if provided, otherwise temp file cleaned up after play
        if args.save:
            play_path = args.save
            tmp_path = None
        else:
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            play_path = tmp.name
            tmp.close()
            Path(play_path).write_bytes(audio)
            tmp_path = play_path
        try:
            subprocess.run(["afplay", play_path], check=True)
            print(f"played locally: {play_path}")
        except Exception as e:
            print(f"afplay failed: {e}", file=sys.stderr)
        finally:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)

    if not args.no_send:
        try:
            send_voice(audio, args.chat, args.caption)
            print(f"sent to {args.chat} ({len(audio)} byte)")
        except Exception as e:
            print(f"TG send failed: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
