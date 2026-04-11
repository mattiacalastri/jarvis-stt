#!/usr/bin/env python3
"""
stt.py — dettatura vocale
Parli → Whisper trascrive → testo incollato (+ Return opzionale).

  python3 ~/scripts/stt.py              # AutoSend ON
  python3 ~/scripts/stt.py --no-send   # solo incolla, niente Return
"""
import argparse
import signal
import subprocess
import sys
import threading
import time
from collections import deque

try:
    import numpy as np
    import sounddevice as sd
    import mlx_whisper
except ImportError as e:
    sys.exit(f"Errore: {e}\npip3 install sounddevice numpy mlx-whisper")

# ── State files (IPC con stt_bar.py) ─────────────────────────────────────────
import pathlib as _pl
_RUN_DIR   = _pl.Path.home() / ".local" / "run" / "jarvis"
_RUN_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE     = _RUN_DIR / "stt_state"
LAST_TEXT_FILE = _RUN_DIR / "stt_last"

def _write_state(state: str) -> None:
    try:
        STATE_FILE.write_text(state)
    except Exception:
        pass

# ── Config ────────────────────────────────────────────────────────────────────
MODEL      = "mlx-community/whisper-small-mlx"
LANG       = "it"
RATE       = 16000
CHUNK      = 512
THRESHOLD  = 0.004
PRE_ROLL   = 6
SILENCE    = 1.5
MIN_DUR    = 0.4
MAX_DUR    = 12.0
COOLDOWN   = 0.5
SEND_DELAY = 1.5

# ── Colori ANSI ───────────────────────────────────────────────────────────────
R  = "\033[0m"        # reset
DIM = "\033[2m"
W  = "\033[1;37m"     # bianco bold
C  = "\033[1;36m"     # cyan
G  = "\033[1;32m"     # verde
Y  = "\033[1;33m"     # giallo
RD = "\033[1;31m"     # rosso
M  = "\033[1;35m"     # magenta

# ── Allucinazioni ─────────────────────────────────────────────────────────────
_HALL_PATTERNS = [
    "sottotitoli", "grazie per aver guardato", "iscriviti",
    "mts srl", "amara.org", "a cura di", "tutti i diritti",
    "www.", ".com", ".it", "youtube", "facebook",
]


def _is_hallucination(text: str) -> bool:
    low = text.lower()
    if any(p in low for p in _HALL_PATTERNS):
        return True
    words = text.split()
    if len(words) < 6:
        return False
    unique = len(set(w.lower().strip(".,!?;:") for w in words))
    return unique / len(words) <= 0.35  # era < 0.30, alzato per catturare "bam×N"


def _log(icon: str, color: str, msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"{DIM}{ts}{R}  {color}{icon}{R}  {msg}", flush=True)


def _paste(text: str, autosend: bool) -> None:
    subprocess.run(["pbcopy"], input=text.encode(), check=True)
    try:
        from pynput.keyboard import Key, Controller
        kb = Controller()
        with kb.pressed(Key.cmd):
            kb.press("v"); kb.release("v")
        if autosend:
            time.sleep(SEND_DELAY)
            kb.press(Key.enter); kb.release(Key.enter)
    except Exception as e:
        _log("⚠", Y, f"paste err: {e}  (testo in clipboard)")


# ── Engine ────────────────────────────────────────────────────────────────────

class Engine:
    def __init__(self, autosend: bool) -> None:
        self._autosend = autosend
        self._buf:    list[np.ndarray] = []
        self._pre     = deque(maxlen=PRE_ROLL)
        self._speaking = False
        self._t_start  = 0.0
        self._t_sil:   float | None = None
        self._t_last   = 0.0
        self._sem      = threading.Semaphore(1)
        self._lock     = threading.Lock()
        self._stop     = threading.Event()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        _log("◌", DIM, "carico modello Whisper tiny…")
        mlx_whisper.transcribe(np.zeros(RATE, dtype=np.float32),
                               path_or_hf_repo=MODEL)

        _write_state("idle")
        mode = f"{G}AutoSend ON{R}" if self._autosend else f"{Y}Solo paste{R}"
        print(
            f"\n  {C}{'─'*44}{R}\n"
            f"  {W}Jarvis STT{R}  {DIM}whisper-tiny · it · {THRESHOLD} RMS{R}\n"
            f"  {mode}  {DIM}·  Ctrl+C per uscire{R}\n"
            f"  {C}{'─'*44}{R}\n",
            flush=True,
        )

        attempt = 0
        while not self._stop.is_set():
            try:
                with sd.InputStream(samplerate=RATE, channels=1,
                                    blocksize=CHUNK, dtype="float32",
                                    callback=self._cb):
                    attempt = 0
                    self._stop.wait()
            except Exception as e:
                if self._stop.is_set():
                    break
                attempt += 1
                wait = min(10 * attempt, 60)
                _log("✗", RD, f"device err: {e}  — retry in {wait}s")
                self._stop.wait(wait)

        _write_state("off")
        print(f"\n  {DIM}ciao.{R}\n", flush=True)

    def stop(self) -> None:
        self._stop.set()

    # ── Audio callback ────────────────────────────────────────────────────────

    def _cb(self, indata, frames, time_info, status) -> None:
        chunk = indata[:, 0].copy()
        rms   = float(np.sqrt(np.mean(chunk ** 2)))
        now   = time.monotonic()

        with self._lock:
            if rms >= THRESHOLD:
                if not self._speaking:
                    self._speaking = True
                    self._t_start  = now
                    self._buf      = list(self._pre)
                    bar = self._rms_bar(rms)
                    _log("●", RD, f"parlato  {bar}")
                    _write_state("recording")
                self._t_sil = None
                self._buf.append(chunk)
                if now - self._t_start >= MAX_DUR:
                    self._finalize(now)
            else:
                self._pre.append(chunk)
                if self._speaking:
                    self._buf.append(chunk)
                    if self._t_sil is None:
                        self._t_sil = now
                    elif now - self._t_sil >= SILENCE:
                        self._finalize(now)

    @staticmethod
    def _rms_bar(rms: float, width: int = 12) -> str:
        filled = min(int(rms / 0.05 * width), width)
        return f"{RD}{'█' * filled}{DIM}{'░' * (width - filled)}{R}"

    # ── Trascrizione ──────────────────────────────────────────────────────────

    def _finalize(self, now: float) -> None:
        dur   = now - self._t_start
        audio = np.concatenate(self._buf) if self._buf else np.zeros(1, dtype=np.float32)
        self._speaking = False
        self._t_sil    = None
        self._buf      = []

        if dur < MIN_DUR:
            return
        if now - self._t_last < COOLDOWN:
            return
        self._t_last = now

        if self._sem.acquire(blocking=False):
            threading.Thread(target=self._transcribe,
                             args=(audio, dur), daemon=True).start()
        else:
            _log("↷", Y, "skip — trascrizione già in corso")

    def _transcribe(self, audio: np.ndarray, dur: float) -> None:
        try:
            _write_state("transcribing")
            _log("⚡", Y, f"trascrivo  {dur:.1f}s…")
            t0     = time.monotonic()
            result = mlx_whisper.transcribe(audio, path_or_hf_repo=MODEL,
                                            language=LANG)
            text    = result.get("text", "").strip()
            elapsed = time.monotonic() - t0

            if not text:
                _write_state("idle")
                return
            if _is_hallucination(text):
                _log("✗", DIM, f"allucinazione scartata  {DIM}({elapsed:.2f}s){R}")
                _write_state("idle")
                return

            send_icon = "↵" if self._autosend else "⎘"
            _log(send_icon, G, f"{W}{text}{R}  {DIM}({elapsed:.2f}s){R}")
            try:
                LAST_TEXT_FILE.write_text(text)
            except Exception:
                pass
            _write_state("idle")
            threading.Thread(target=_paste, args=(text, self._autosend),
                             daemon=True).start()
        finally:
            self._sem.release()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="Jarvis STT — dettatura vocale")
    p.add_argument("--no-send", action="store_true",
                   help="incolla senza premere Return")
    args = p.parse_args()

    engine = Engine(autosend=not args.no_send)

    def _sig(*_):
        engine.stop()

    signal.signal(signal.SIGTERM, _sig)
    signal.signal(signal.SIGINT,  _sig)
    engine.run()


if __name__ == "__main__":
    main()
