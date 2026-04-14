#!/usr/bin/env python3
"""
stt_menubar.py — Mini menu bar per controllare stt.py daemon
Non ha pipeline audio proprio — legge lo STATE_FILE di stt.py e permette
start/stop del daemon.

Stati:
  idle         → 🎙 (disponibile, daemon up)
  parlato      → 🔴 (sta registrando)
  transcribing → ⚡ (whisper sta elaborando)
  off          → 🔇 (daemon non running)
"""
import os
import signal
import subprocess
import time
from pathlib import Path

import rumps

RUN_DIR = Path.home() / ".local" / "run" / "jarvis"
STATE_FILE = RUN_DIR / "stt_state"
LAST_TEXT = RUN_DIR / "stt_last"
PID_FILE = RUN_DIR / "stt.pid"

VENV_PY = str(Path.home() / "scripts/.venv-stt/bin/python")
STT_SCRIPT = str(Path.home() / "scripts/stt.py")

ICONS = {
    "off": "🔇",
    "idle": "🎙",
    "parlato": "🔴",
    "transcribing": "⚡",
}


def read_state() -> str:
    try:
        return STATE_FILE.read_text().strip()
    except Exception:
        return "off"


def daemon_pid() -> int | None:
    try:
        out = subprocess.check_output(["pgrep", "-f", "scripts/stt.py"], text=True)
        pids = [int(p) for p in out.split() if p.strip().isdigit()]
        return pids[0] if pids else None
    except Exception:
        return None


def start_daemon() -> None:
    if daemon_pid():
        return
    subprocess.Popen(
        [VENV_PY, STT_SCRIPT, "--no-send"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def stop_daemon() -> None:
    try:
        out = subprocess.check_output(["pgrep", "-f", "scripts/stt.py"], text=True)
        pids = [int(p) for p in out.split() if p.strip().isdigit()]
    except Exception:
        pids = []
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
    time.sleep(0.8)
    try:
        out = subprocess.check_output(["pgrep", "-f", "scripts/stt.py"], text=True)
        survivors = [int(p) for p in out.split() if p.strip().isdigit()]
    except Exception:
        survivors = []
    for pid in survivors:
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass
    # Clear state so icon goes to OFF immediately
    try:
        STATE_FILE.write_text("off")
    except Exception:
        pass


class STTBar(rumps.App):
    def __init__(self):
        super().__init__("🎙 STT", quit_button=None)
        self.menu = [
            "Stato: ...",
            "Ultimo: -",
            None,
            rumps.MenuItem("▶ Start daemon", callback=self.on_start),
            rumps.MenuItem("⏸ Stop daemon", callback=self.on_stop),
            rumps.MenuItem("↻ Restart daemon", callback=self.on_restart),
            None,
            rumps.MenuItem("Quit menu bar", callback=self.on_quit),
        ]
        self._tick()

    @rumps.timer(1.0)
    def _tick(self, _=None):
        pid = daemon_pid()
        state = read_state() if pid else "off"
        icon = ICONS.get(state, "🎙")
        self.title = icon
        self.menu["Stato: ..."].title = f"Stato: {state}" + (f" (pid {pid})" if pid else "")
        try:
            last = LAST_TEXT.read_text().strip()[:60]
            if last:
                self.menu["Ultimo: -"].title = f"Ultimo: {last}"
        except Exception:
            pass

    def on_start(self, _):
        start_daemon()
        rumps.notification("Jarvis STT", "Daemon avviato", "Parla in italiano, paste auto")

    def on_stop(self, _):
        stop_daemon()
        rumps.notification("Jarvis STT", "Daemon fermato", "Mic disattivo")

    def on_restart(self, _):
        stop_daemon()
        time.sleep(0.5)
        start_daemon()
        rumps.notification("Jarvis STT", "Daemon riavviato", "")

    def on_quit(self, _):
        rumps.quit_application()


if __name__ == "__main__":
    STTBar().run()
