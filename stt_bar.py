#!/usr/bin/env python3
"""
stt_bar.py — menu bar per stt.py

Icona live:  🔇 spento  |  🎙 ascolto  |  🔴 registra  |  ⚡ trascrivo
Tick 1s: legge ~/.local/run/jarvis/stt_state e stt_last per aggiornare UI.
"""
import subprocess
import sys
import threading
from pathlib import Path

import rumps

STT    = Path.home() / "scripts" / "stt.py"
PYTHON = sys.executable

_RUN_DIR       = Path.home() / ".local" / "run" / "jarvis"
STATE_FILE     = _RUN_DIR / "stt_state"
LAST_TEXT_FILE = _RUN_DIR / "stt_last"

STATE_ICONS = {
    "idle":         "🎙",
    "recording":    "🔴",
    "transcribing": "⚡",
    "off":          "🔇",
}
STATE_LABELS = {
    "idle":         "In ascolto",
    "recording":    "Registra…",
    "transcribing": "Trascrivo…",
    "off":          "Spento",
}


class STTBar(rumps.App):
    def __init__(self) -> None:
        super().__init__("🔇", quit_button=None)
        self._proc: subprocess.Popen | None = None
        self._autosend = True

        self._toggle_item = rumps.MenuItem("▶ Avvia",     callback=self.toggle)
        self._send_item   = rumps.MenuItem("✅ AutoSend", callback=self.toggle_autosend)
        self._status_item = rumps.MenuItem("Spento",      callback=None)
        self._last_item   = rumps.MenuItem("—",           callback=None)

        self.menu = [
            self._toggle_item,
            self._send_item,
            None,
            self._status_item,
            self._last_item,
            None,
            rumps.MenuItem("Esci", callback=rumps.quit_application),
        ]

        rumps.Timer(self._tick, 1.0).start()

    # ── helpers ───────────────────────────────────────────────────────────────

    def _is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def _start(self) -> None:
        args = [PYTHON, str(STT)]
        if not self._autosend:
            args.append("--no-send")
        self._proc = subprocess.Popen(args)
        self._toggle_item.title = "⏹ Ferma"

    def _stop(self) -> None:
        if self._proc:
            self._proc.terminate()
            self._proc = None
        self.title = "🔇"
        self._toggle_item.title = "▶ Avvia"
        self._status_item.title = "Spento"
        try:
            STATE_FILE.write_text("off")
        except Exception:
            pass

    # ── tick (ogni secondo) ───────────────────────────────────────────────────

    def _tick(self, _) -> None:
        if not self._is_running():
            self.title = "🔇"
            self._status_item.title = "Spento"
            return

        # leggi stato
        try:
            state = STATE_FILE.read_text().strip()
        except Exception:
            state = "idle"

        self.title = STATE_ICONS.get(state, "🎙")
        self._status_item.title = STATE_LABELS.get(state, state)

        # ultimo testo trascritto
        try:
            last = LAST_TEXT_FILE.read_text().strip()
            if last:
                preview = last[:50] + "…" if len(last) > 50 else last
                self._last_item.title = f"💬 {preview}"
        except Exception:
            pass

    # ── actions ───────────────────────────────────────────────────────────────

    def toggle(self, _) -> None:
        if self._is_running():
            threading.Thread(target=self._stop, daemon=True).start()
        else:
            threading.Thread(target=self._start, daemon=True).start()

    def toggle_autosend(self, _) -> None:
        self._autosend = not self._autosend
        self._send_item.title = f"{'✅' if self._autosend else '⬜'} AutoSend"
        if self._is_running():
            self._stop()
            self._start()


if __name__ == "__main__":
    try:
        import AppKit
        AppKit.NSBundle.mainBundle().infoDictionary()["LSUIElement"] = "1"
    except Exception:
        pass
    STTBar().run()
