#!/usr/bin/env python3
"""
stt_bar.py — Jarvis STT menu bar
Backend: Apple SFSpeechRecognizer (Neural Engine, no MLX crash).
Icona: 🔇 spento | 📡 calibra | 🎙+wave idle | 🔴+wave registra | ⚡+wave trascrivo
"""
import os
import tempfile
import threading
import time
import wave
from collections import deque
from pathlib import Path

import numpy as np
import rumps
import sounddevice as sd
from scipy.signal import resample_poly

# ── Paths ──────────────────────────────────────────────────────────────────────
_RUN_DIR       = Path.home() / ".local" / "run" / "jarvis"
_RUN_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE     = _RUN_DIR / "stt_state"
LAST_TEXT_FILE = _RUN_DIR / "stt_last"

# ── Config ─────────────────────────────────────────────────────────────────────
LANG        = "it-IT"
DEVICE_RATE = 48000
TARGET_RATE = 16000
CHUNK       = 1024
PRE_ROLL    = 6
SILENCE     = 1.5
MIN_DUR     = 0.8
MAX_DUR     = 12.0
COOLDOWN    = 0.5
WAVE_COLS   = 5       # numero di barre nel display live
SEND_DELAY  = 1.5     # secondi dopo il paste prima di premere Return (autosend)

_BARS = "▁▂▃▄▅▆▇█"

_HALL_PATTERNS = [
    "sottotitoli", "grazie per aver guardato", "iscriviti",
    "mts srl", "amara.org", "a cura di", "tutti i diritti",
    "www.", ".com", ".it", "youtube", "facebook",
    "grazie a tutti", "grazie mille", "grazie per l'attenzione",
    "buona giornata", "buonasera a tutti", "benvenuti",
    "a presto", "arrivederci", "ciao a tutti",
    "vi ringrazio", "grazie ancora", "un saluto",
    "in bocca al lupo", "tanti auguri",
]
# Exact-match (strip punct, lowercase)
_HALL_EXACT = {"grazie", "prego", "okay", "sì", "si", "no", "ciao"}


def _is_hallucination(text: str) -> bool:
    low = text.lower()
    if any(p in low for p in _HALL_PATTERNS):
        return True
    core = text.strip().lower().replace(" ", "")
    if core and len(set(core)) <= 3:
        return True
    stripped = low.strip(".,!?;: ")
    if stripped in _HALL_EXACT:
        return True
    words = text.split()
    if len(words) < 6:
        return False
    unique = len(set(w.lower().strip(".,!?;:") for w in words))
    return unique / len(words) <= 0.35


# ── Speech Recognition ─────────────────────────────────────────────────────────

def _request_speech_permission() -> bool:
    try:
        import Speech
        status = Speech.SFSpeechRecognizer.authorizationStatus()
        # 3 = authorized
        if status == 3:
            return True
        if status == 0:  # notDetermined
            done = threading.Event()
            result = [False]
            def handler(s):
                result[0] = (s == 3)
                done.set()
            Speech.SFSpeechRecognizer.requestAuthorization_(handler)
            done.wait(30)
            return result[0]
        return False
    except Exception:
        return True


def _save_wav(audio: np.ndarray, rate: int = TARGET_RATE) -> str:
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False, dir="/tmp")
    tmp.close()
    with wave.open(tmp.name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm.tobytes())
    return tmp.name


# Script inline per il subprocess — ha il suo main thread + RunLoop proprio
_TRANSCRIBE_SCRIPT = r"""
import sys, time
wav_path = sys.argv[1]
lang     = sys.argv[2] if len(sys.argv) > 2 else "it-IT"
try:
    import Foundation, Speech, AppKit
    pool = Foundation.NSAutoreleasePool.alloc().init()
    url      = Foundation.NSURL.fileURLWithPath_(wav_path)
    locale   = Foundation.NSLocale.localeWithLocaleIdentifier_(lang)
    rec      = Speech.SFSpeechRecognizer.alloc().initWithLocale_(locale)
    if not rec or not rec.isAvailable():
        sys.exit(0)
    req = Speech.SFSpeechURLRecognitionRequest.alloc().initWithURL_(url)
    req.setShouldReportPartialResults_(False)
    done = [False]; text = [""]
    def cb(result, error):
        if result:
            text[0] = str(result.bestTranscription().formattedString())
        done[0] = True
    task = rec.recognitionTaskWithRequest_resultHandler_(req, cb)
    loop     = AppKit.NSRunLoop.currentRunLoop()
    deadline = time.time() + 15
    while not done[0] and time.time() < deadline:
        loop.runMode_beforeDate_(AppKit.NSDefaultRunLoopMode,
                                 Foundation.NSDate.dateWithTimeIntervalSinceNow_(0.1))
    if not done[0]:
        task.cancel()
    del pool
    print(text[0], end="")
except Exception as e:
    sys.stderr.write(str(e))
    sys.exit(1)
"""

_PYTHON = "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"


def _transcribe_wav(wav_path: str) -> str:
    import subprocess
    try:
        r = subprocess.run(
            [_PYTHON, "-c", _TRANSCRIBE_SCRIPT, wav_path, LANG],
            capture_output=True, text=True, timeout=20,
        )
        if r.stderr:
            try:
                (_RUN_DIR / "stt_err.txt").write_text(r.stderr[:500])
            except Exception:
                pass
        return r.stdout.strip()
    except Exception as e:
        try:
            (_RUN_DIR / "stt_err.txt").write_text(f"subprocess error: {e}")
        except Exception:
            pass
        return ""


# ── Paste ──────────────────────────────────────────────────────────────────────

def _paste(text: str, autosend: bool = False) -> None:
    import subprocess
    # 1. Copia negli appunti
    subprocess.run(["pbcopy"], input=text.encode(), check=True)
    # 2. CMD+V via osascript — subprocess isolato, ObjC crash non uccide il parent
    try:
        subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to keystroke "v" using command down'],
            timeout=3, capture_output=True
        )
        if autosend:
            time.sleep(SEND_DELAY)
            subprocess.run(
                ["osascript", "-e",
                 'tell application "System Events" to key code 36'],
                timeout=3, capture_output=True
            )
    except Exception:
        pass


# ── Mic permission ─────────────────────────────────────────────────────────────

def _request_mic_permission() -> bool:
    try:
        from AVFoundation import (
            AVCaptureDevice, AVMediaTypeAudio,
            AVAuthorizationStatusAuthorized,
            AVAuthorizationStatusNotDetermined,
        )
        status = AVCaptureDevice.authorizationStatusForMediaType_(AVMediaTypeAudio)
        if status == AVAuthorizationStatusAuthorized:
            return True
        if status == AVAuthorizationStatusNotDetermined:
            done = threading.Event()
            result = [False]
            def _handler(granted):
                result[0] = bool(granted)
                done.set()
            AVCaptureDevice.requestAccessForMediaType_completionHandler_(
                AVMediaTypeAudio, _handler
            )
            done.wait(30)
            return result[0]
        return False
    except Exception:
        return True


# ── Audio Engine ───────────────────────────────────────────────────────────────

class Engine:
    def __init__(self) -> None:
        self._buf: list[np.ndarray] = []
        self._pre       = deque(maxlen=PRE_ROLL)
        self._speaking  = False
        self._t_start   = 0.0
        self._t_sil: float | None = None
        self._t_last    = 0.0
        self._sem       = threading.Semaphore(1)
        self._lock      = threading.Lock()
        self._stop      = threading.Event()
        self._stop.set()
        self._autosend  = False
        self._threshold = 0.015
        self._state     = "off"
        self._rms_wave  = deque([0.0] * WAVE_COLS, maxlen=WAVE_COLS)
        # Throttle wave updates to ~10Hz (every 5 chunks at 48kHz/1024)
        self._wave_tick = 0

    def get_state(self) -> str:
        return self._state

    def get_wave(self) -> str:
        """Return live waveform string of WAVE_COLS bars."""
        result = ""
        for r in self._rms_wave:
            if r < 0.003:
                result += "·"
            else:
                idx = min(int(r / 0.06 * 8), 7)
                result += _BARS[idx]
        return result

    def _set_state(self, state: str, no_io: bool = False) -> None:
        self._state = state
        if no_io:
            return
        try:
            STATE_FILE.write_text(state)
        except Exception:
            pass

    def start(self, autosend: bool = False, on_cal_level=None) -> None:
        self._autosend     = autosend
        self._on_cal_level = on_cal_level or (lambda rms: None)
        self._set_state("calibrating")
        self._stop.clear()
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self) -> None:
        self._stop.set()

    def is_active(self) -> bool:
        return not self._stop.is_set()

    def _run(self) -> None:
        # Calibrazione: 1.5s di audio per calcolare soglia ambiente
        cal_buf: list[float] = []
        cal_done = threading.Event()

        def _cal_cb(indata, frames, time_info, status):
            try:
                # Decimazione semplice in callback (no scipy in realtime)
                chunk = indata[:, 0][::3].astype(np.float32)
                rms   = float(np.sqrt(np.mean(chunk ** 2)))
                cal_buf.append(rms)
                self._rms_wave.append(rms)   # deque è thread-safe
                if len(cal_buf) >= int(DEVICE_RATE / CHUNK * 1.5):
                    cal_done.set()
            except Exception:
                pass

        try:
            with sd.InputStream(samplerate=DEVICE_RATE, channels=1,
                                blocksize=CHUNK, dtype="float32",
                                callback=_cal_cb):
                cal_done.wait(timeout=5)
        except Exception:
            self._set_state("err:mic")
            self._stop.set()
            return

        if not cal_buf or max(cal_buf) < 1e-6:
            self._set_state("err:mic")
            self._stop.set()
            return

        self._threshold = max(0.015, float(np.mean(cal_buf)) * 6.0)
        try:
            (_RUN_DIR / "stt_diag.txt").write_text(
                f"threshold={self._threshold:.6f} cal_mean={float(np.mean(cal_buf)):.6f} cal_max={max(cal_buf):.6f}"
            )
        except Exception:
            pass
        self._set_state("idle")

        # Loop principale
        while not self._stop.is_set():
            try:
                with sd.InputStream(samplerate=DEVICE_RATE, channels=1,
                                    blocksize=CHUNK, dtype="float32",
                                    callback=self._audio_cb):
                    self._stop.wait()
            except Exception:
                if self._stop.is_set():
                    break
                time.sleep(3)

        self._set_state("off")

    def _audio_cb(self, indata, frames, time_info, status) -> None:
        try:
            chunk = indata[:, 0][::3].astype(np.float32)   # decimazione leggera in callback
            rms   = float(np.sqrt(np.mean(chunk ** 2)))
            now   = time.monotonic()
            do_finalize = False

            with self._lock:
                self._wave_tick += 1
                if self._wave_tick >= 5:
                    self._wave_tick = 0
                    self._rms_wave.append(rms)

                if rms >= self._threshold:
                    if not self._speaking:
                        self._speaking = True
                        self._t_start  = now
                        self._buf      = list(self._pre)
                        self._state    = "recording"   # no I/O in callback
                    self._t_sil = None
                    self._buf.append(chunk)
                    if now - self._t_start >= MAX_DUR:
                        do_finalize = True
                else:
                    self._pre.append(chunk)
                    if self._speaking:
                        self._buf.append(chunk)
                        if self._t_sil is None:
                            self._t_sil = now
                        elif now - self._t_sil >= SILENCE:
                            do_finalize = True

            if do_finalize:
                self._finalize(now)   # fuori dal lock, può fare I/O e thread
        except Exception:
            pass

    def _finalize(self, now: float) -> None:
        with self._lock:
            dur   = now - self._t_start
            audio = np.concatenate(self._buf) if self._buf else np.zeros(1, dtype=np.float32)
            self._speaking = False
            self._t_sil    = None
            self._buf      = []

        if dur < MIN_DUR or now - self._t_last < COOLDOWN:
            self._state = "idle"   # il tick scriverà su file
            return
        self._t_last = now

        if self._sem.acquire(blocking=False):
            threading.Thread(target=self._transcribe, args=(audio,), daemon=True).start()

    def _transcribe(self, audio: np.ndarray) -> None:
        wav_path = None
        try:
            self._set_state("transcribing")
            wav_path = _save_wav(audio)
            text = _transcribe_wav(wav_path)

            try:
                (_RUN_DIR / "stt_raw.txt").write_text(
                    f"[{time.strftime('%H:%M:%S')}] hall={_is_hallucination(text)} text={repr(text)}"
                )
            except Exception:
                pass

            if text and not _is_hallucination(text):
                try:
                    LAST_TEXT_FILE.write_text(text)
                except Exception:
                    pass
                self._set_state("idle")
                threading.Thread(target=_paste, args=(text, self._autosend),
                                 daemon=True).start()
            else:
                self._set_state("idle")
        finally:
            if wav_path:
                try: os.unlink(wav_path)
                except Exception: pass
            self._sem.release()


# ── Menu bar ───────────────────────────────────────────────────────────────────

class STTBar(rumps.App):
    def __init__(self) -> None:
        super().__init__("🔇", quit_button=None)
        self._engine       = Engine()
        self._autosend     = False
        self._auto_started = False

        self._toggle_item = rumps.MenuItem("▶ Avvia",     callback=self.toggle)
        self._send_item   = rumps.MenuItem("⬜ AutoSend", callback=self.toggle_autosend)
        self._status_item = rumps.MenuItem("Spento",      callback=None)
        self._last_item   = rumps.MenuItem("—",           callback=None)

        self.menu = [
            self._toggle_item,
            self._send_item,
            None,
            self._status_item,
            self._last_item,
            None,
            rumps.MenuItem("Esci", callback=self._quit),
        ]

        rumps.Timer(self._tick, 0.15).start()
        rumps.Timer(self._auto_start, 1.5).start()

    def _tick(self, _) -> None:
        if not self._engine.is_active():
            self.title = "🔇"
            self._toggle_item.title = "▶ Avvia"
            self._status_item.title = "Spento"
            return

        state = self._engine.get_state()
        wave  = self._engine.get_wave()

        if state == "err:mic":
            self.title = "⚠️"
            self._status_item.title = "Mic non rilevato"
            return

        if state == "calibrating":
            self.title = f"📡{wave}"
            self._status_item.title = "Calibrazione…"
            return

        icons = {"idle": "🎙", "recording": "🔴", "transcribing": "⚡"}
        labels = {"idle": "In ascolto", "recording": "Registra…", "transcribing": "Trascrivo…"}

        self.title = f"{icons.get(state, '🎙')}{wave}"
        self._status_item.title = labels.get(state, state)

        try:
            last = LAST_TEXT_FILE.read_text().strip()
            if last:
                preview = last[:50] + "…" if len(last) > 50 else last
                self._last_item.title = f"💬 {preview}"
        except Exception:
            pass

    def _auto_start(self, _) -> None:
        if self._auto_started or self._engine.is_active():
            return
        self._auto_started = True
        if not _request_mic_permission():
            self.title = "⚠️"
            self._status_item.title = "Mic non autorizzato"
            rumps.notification("Jarvis STT", "Microfono negato",
                               "Vai in Impostazioni → Privacy → Microfono", sound=False)
            return
        _request_speech_permission()
        self.toggle(None)

    def toggle(self, _) -> None:
        if self._engine.is_active():
            self._engine.stop()
            self.title = "🔇"
            self._toggle_item.title = "▶ Avvia"
            self._status_item.title = "Spento"
        else:
            self._toggle_item.title = "⏹ Ferma"
            self._status_item.title = "Calibrazione…"
            rumps.notification("Jarvis STT", "Calibrazione microfono",
                               "Resta in silenzio 2 secondi…", sound=False)
            self._engine.start(autosend=self._autosend)

    def toggle_autosend(self, _) -> None:
        self._autosend = not self._autosend
        self._send_item.title = f"{'✅' if self._autosend else '⬜'} AutoSend"
        if self._engine.is_active():
            self._engine._autosend = self._autosend

    def _quit(self, _) -> None:
        (_RUN_DIR / "stt_disabled").touch()
        self._engine.stop()
        rumps.quit_application()


if __name__ == "__main__":
    import sys

    if os.environ.get("XPC_SERVICE_NAME") == "com.jarvis.menubar":
        sys.exit(0)

    _DISABLED_FILE = _RUN_DIR / "stt_disabled"
    if _DISABLED_FILE.exists():
        sys.exit(0)

    _PID_FILE = _RUN_DIR / "stt_bar.pid"
    try:
        if _PID_FILE.exists():
            old_pid = int(_PID_FILE.read_text().strip())
            try:
                os.kill(old_pid, 0)
                sys.exit(0)
            except ProcessLookupError:
                pass
    except Exception:
        pass
    _DISABLED_FILE.unlink(missing_ok=True)
    _PID_FILE.write_text(str(os.getpid()))

    try:
        import AppKit
        AppKit.NSBundle.mainBundle().infoDictionary()["LSUIElement"] = "1"
    except Exception:
        pass
    try:
        STTBar().run()
    finally:
        try:
            _PID_FILE.unlink()
        except Exception:
            pass
