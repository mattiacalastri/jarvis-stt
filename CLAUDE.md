# jarvis-stt

Voice agent Jarvis del sistema Polpo — STT (whisper/mlx-whisper + VAD), TTS (ElevenLabs Andy M default), autosend daemon, menu bar JarvisToggle.app.

## Scope
Canale voce bidirezionale Mattia ↔ Polpo. Pipeline: dictation → trascrizione → routing skill → voice response (ElevenLabs). Distinto da `claude-voice` (Astra OS voice agents per clienti — Marco GEO outbound, ecc.).

## Ground Truth
- Owner: Mattia Calastri / sistema Polpo
- Memory index: `~/.claude/projects/-Users-mattiacalastri-projects/memory/MEMORY.md`
- Default voice: Andy M (ElevenLabs). Palette: Callum/George/Bill/Laura/Roger/Mimmi.
- Audio tag v3 auto-switch in `voice_briefing.py`.
- Runtime files: `~/.local/run/jarvis/`.
- LaunchAgent: `com.jarvis.autosend`, `com.jarvis.stt-bar`.

## Rules
- Naming kebab-case con `-` come separatore.
- Mai toccare LaunchAgent o file in `~/.local/run/jarvis/` senza invocare agent `jarvis-voice-agent`.
- Skill correlate: `dictation-mode` (modalità voce bidirezionale).
- Test harness auto-evolutivo: 6/6 verde target.
- Fallback: `--piper` solo se ElevenLabs 401/429.

## Pre-flight
- `launchctl list | grep jarvis` per stato daemon.
- `ls ~/.local/run/jarvis/` per runtime files.
- Verifica ElevenLabs quota prima di test heavy.

## Stato reale (verificato sess.1809 — 2026-05-12)
- **GitHub remote**: `mattiacalastri/jarvis-stt`
- **Stack**: Python (`requirements.txt`)
- **Architettura 3-layer**:
  - `stt.py` — core STT engine (whisper/mlx-whisper)
  - `stt_bar.py` — menu bar STT toggle
  - `stt_menubar.py` — variant menubar UI
- **Voice entry point**: `voice_briefing.py` (chiamato da hook + skill come `garden-walk`)
- **Calibration**: `jarvis_calibrate.py`
- **LaunchAgent incluso nel repo**: `com.jarvis.stt.plist`
- **Test harness**: `test_harness/` (target 6/6 verde — regression scenari voice)
- **Asset audio**: `assets/`
- **Doc**: `README.md`
- **Last commit**: `a1a3148 test(harness): regression scenario per call frontmost guard voice_briefing.py (sess.1577)`
