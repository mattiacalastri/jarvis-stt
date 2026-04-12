<p align="center">
  <strong>Jarvis STT</strong>
</p>

<h3 align="center">Voice dictation for Claude Code. Speak. Text appears. Press nothing.</h3>

<p align="center">
  On-device. Instant. No API key. No MLX crash. Built in the forge.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-teal.svg" alt="MIT"></a>
  <img src="https://img.shields.io/badge/macOS-12%2B-black.svg" alt="macOS 12+">
  <img src="https://img.shields.io/badge/Backend-SFSpeechRecognizer-blue.svg" alt="SFSpeechRecognizer">
  <img src="https://img.shields.io/badge/Works%20with-Claude%20Code-white.svg" alt="Claude Code">
  <img src="https://img.shields.io/badge/Sessions-885%2B-white.svg" alt="885+ Sessions">
</p>

---

## The Problem

Claude Code lives in the terminal. Long prompts break flow.

You stop thinking about the problem and start thinking about typing. The model is ready. The model has been ready. **Your hands are the bottleneck.**

Every word you type is a word you didn't think.

---

## The Solution

Speak your prompt. Jarvis transcribes it on-device, pastes it into Claude Code, and (optionally) hits Return. The thought goes directly to the model. Nothing in between.

```
Microphone → Apple Neural Engine → clipboard → Cmd+V → (Return)
```

No API key. No model download. No data leaves your machine.

---

## What you see in your menubar

```
🔇            → off
📡·▁▂▁·       → calibrating (reading your room noise)
🎙·▁▂▃·       → idle / listening
🔴▄▆█▅        → recording your voice
⚡▂▄▃▁        → transcribing
```

The waveform bars are live — always showing your current mic level.

---

## Origin

This tool was extracted from 885 sessions of building an AI-driven operating system with Claude.

At some point the friction was no longer the model — it was the distance between thought and input. Voice removed that distance.

The first version used Whisper MLX. It worked — until it didn't. Metal/MLX crashes under RAM pressure leave no traceback. A dead process, no text, no error. Not acceptable for a daily driver.

`SFSpeechRecognizer` is the same engine behind macOS dictation. It's stable because Apple needs it to be stable. Same accuracy for Italian and English. Zero model download.

Part of the [AI Forging Kit](https://github.com/mattiacalastri/AI-Forging-Kit) emerging from 885 sessions.

---

## Features

| Feature | Description |
|---------|-------------|
| **On-device** | Apple Neural Engine — no API key, no cloud, no model download |
| **Live waveform** | Always-visible bars in menubar showing mic level |
| **AutoSend toggle** | Optional: paste + Return automatically (toggle in menu) |
| **Auto-calibration** | Reads your room noise on start, sets threshold automatically |
| **Hallucination filter** | Drops common STT artifacts and repetition loops |
| **Pre-roll buffer** | Never clips the first syllable |
| **One-click stop** | No hunting for a terminal |

---

## Requirements

- macOS 12+ (any hardware — not just Apple Silicon)
- Python 3.11+
- Microphone

```bash
pip3 install rumps sounddevice numpy scipy \
             pyobjc-framework-Speech pyobjc-framework-AVFoundation \
             pynput
```

**Permissions** (macOS will prompt on first run):
- Microphone — audio capture
- Speech Recognition — SFSpeechRecognizer
- Accessibility — Cmd+V paste via pynput

---

## Run

```bash
# Must run in an Aqua (desktop) session — use osascript:
osascript -e 'do shell script "python3 /path/to/stt_bar.py &"'
```

Or add `com.jarvis.stt.plist` to `~/Library/LaunchAgents/` (edit the path inside first).

---

## Calibrate your mic first

```bash
python3 jarvis_calibrate.py
```

Speak, whisper, stay quiet — 30 seconds. It prints RMS levels live and suggests your threshold.

The app auto-calibrates on every start (1.5s of silence). This script is for when you want to fine-tune.

---

## Configuration

Constants at the top of `stt_bar.py`:

| Variable | Default | Notes |
|----------|---------|-------|
| `LANG` | `"it-IT"` | Any locale SFSpeechRecognizer supports (`en-US`, `fr-FR`…) |
| `SILENCE` | `1.5` | Seconds of quiet before finalizing |
| `MIN_DUR` | `0.8` | Minimum recording duration (rejects claps, pops) |
| `MAX_DUR` | `12.0` | Hard cap per utterance |
| `SEND_DELAY` | `1.5` | Pause before hitting Return (when AutoSend is on) |
| `WAVE_COLS` | `5` | Number of waveform bars in menubar |

---

## AutoSend

Click **AutoSend** in the menubar menu to toggle.

- **OFF** (default): transcription is pasted into the focused app. You press Return.
- **ON**: transcription is pasted, then Return is pressed automatically after `SEND_DELAY` seconds.

Useful when you're dictating prompts into Claude Code and want fully hands-free operation.

---

## Hallucination filter

Common STT outputs on silence or background noise are suppressed:

- Known Italian patterns: "Grazie a tutti", "Buona giornata", "Arrivederci"…
- Single-word outputs: "Grazie.", "Sì.", "No."…
- Repetition loops: ≤3 unique characters, or unique-word ratio ≤ 0.35

---

## See Also

- [AI Forging Kit](https://github.com/mattiacalastri/AI-Forging-Kit) — the method to forge your AI into a partner
- [EGI — Emergent General Intelligence](https://github.com/mattiacalastri/EGI-Emergent-General-Intelligence) — the theory behind why context beats architecture

---

## License

MIT — use it, ship it, build on it.

---

<p align="center">
  <em>"The bottleneck was never the model."</em>
  <br><br>
  — Mattia Calastri, 2026
</p>
