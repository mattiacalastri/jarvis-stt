<!--
SEO Keywords: claude code, voice dictation, whisper, apple silicon, macos, offline stt,
speech recognition, sfspeechrecognizer, menubar, on-device ai, italian ai, astra digital,
jarvis, polpo squad, anthropic
SEO Description: Offline voice dictation for Claude Code. Speak, text appears in your terminal. On-device, menu bar, zero cloud. Built by Astra Digital.
Author: Mattia Calastri
Location: Verona, Italy
-->

<div align="center">

# 🐙 Jarvis STT

### Voice dictation for Claude Code. Speak. Text appears. Press nothing.

On-device. Instant. No API key. No cloud. Built in the forge.

[![License](https://img.shields.io/badge/License-MIT-00d4aa?labelColor=0a0f1a)](./LICENSE)
[![Stars](https://img.shields.io/github/stars/mattiacalastri/jarvis-stt?color=00d4aa&labelColor=0a0f1a)](https://github.com/mattiacalastri/jarvis-stt/stargazers)
[![macOS](https://img.shields.io/badge/macOS-12+-00d4aa?labelColor=0a0f1a&logo=apple&logoColor=white)](https://www.apple.com/macos/)
[![Backend](https://img.shields.io/badge/backend-SFSpeechRecognizer-00d4aa?labelColor=0a0f1a)](#)
[![Sessions](https://img.shields.io/badge/sessions-900+-00d4aa?labelColor=0a0f1a)](#)
[![Astra Digital](https://img.shields.io/badge/built_by-Astra_Digital-00d4aa?labelColor=0a0f1a)](https://mattiacalastri.com)

</div>

---

## ✨ Why

Claude Code lives in the terminal. Long prompts break flow.

You stop thinking about the problem and start thinking about typing. The model is ready. The model has been ready. **Your hands are the bottleneck.**

Every word you type is a word you didn't think.

## 🎯 What it does

Speak your prompt. Jarvis transcribes it on-device, pastes it into Claude Code, and (optionally) hits Return. The thought goes directly to the model. Nothing in between.

```
Microphone → Apple Neural Engine → clipboard → Cmd+V → (Return)
```

No API key. No model download. No data leaves your machine.

## 📟 What you see in your menubar

```
🔇            → off
📡·▁▂▁·       → calibrating (reading your room noise)
🎙·▁▂▃·       → idle / listening
🔴▄▆█▅        → recording your voice
⚡▂▄▃▁        → transcribing
```

The waveform bars are live — always showing your current mic level.

## 🚀 Quick Start

```bash
pip3 install rumps sounddevice numpy scipy \
             pyobjc-framework-Speech pyobjc-framework-AVFoundation \
             pynput

# Must run in an Aqua (desktop) session — use osascript:
osascript -e 'do shell script "python3 /path/to/stt_bar.py &"'
```

Or add `com.jarvis.stt.plist` to `~/Library/LaunchAgents/` (edit the path inside first).

**Permissions** (macOS prompts on first run): Microphone · Speech Recognition · Accessibility.

## 🎯 Features

| Feature | Description |
|---------|-------------|
| 🐙 **On-device** | Apple Neural Engine — no API key, no cloud, no model download |
| 📊 **Live waveform** | Always-visible bars in menubar showing mic level |
| ⚡ **AutoSend toggle** | Optional: paste + Return automatically (toggle in menu) |
| 🎚️ **Auto-calibration** | Reads your room noise on start, sets threshold automatically |
| 🛡️ **Hallucination filter** | Drops common STT artifacts and repetition loops |
| 🔄 **Pre-roll buffer** | Never clips the first syllable |
| 🛑 **One-click stop** | No hunting for a terminal |

## 🏗️ Origin

This tool was extracted from 900+ sessions of building an AI-driven operating system with Claude.

At some point the friction was no longer the model — it was the distance between thought and input. Voice removed that distance.

The first version used Whisper MLX. It worked — until it didn't. Metal/MLX crashes under RAM pressure leave no traceback. A dead process, no text, no error. Not acceptable for a daily driver.

`SFSpeechRecognizer` is the same engine behind macOS dictation. It's stable because Apple needs it to be stable. Same accuracy for Italian and English. Zero model download.

## 🎚️ Calibrate your mic first

```bash
python3 jarvis_calibrate.py
```

Speak, whisper, stay quiet — 30 seconds. It prints RMS levels live and suggests your threshold. The app auto-calibrates on every start (1.5s of silence). This script is for when you want to fine-tune.

## ⚙️ Configuration

Constants at the top of `stt_bar.py`:

| Variable | Default | Notes |
|----------|---------|-------|
| `LANG` | `"it-IT"` | Any locale SFSpeechRecognizer supports (`en-US`, `fr-FR`…) |
| `SILENCE` | `1.5` | Seconds of quiet before finalizing |
| `MIN_DUR` | `0.8` | Minimum recording duration (rejects claps, pops) |
| `MAX_DUR` | `12.0` | Hard cap per utterance |
| `SEND_DELAY` | `1.5` | Pause before hitting Return (when AutoSend is on) |
| `WAVE_COLS` | `5` | Number of waveform bars in menubar |

## 🔊 AutoSend

Click **AutoSend** in the menubar menu to toggle.

- **OFF** (default): transcription is pasted into the focused app. You press Return.
- **ON**: transcription is pasted, then Return is pressed automatically after `SEND_DELAY` seconds.

Useful when you're dictating prompts into Claude Code and want fully hands-free operation.

## 🛡️ Hallucination filter

Common STT outputs on silence or background noise are suppressed:

- Known Italian patterns: "Grazie a tutti", "Buona giornata", "Arrivederci"…
- Single-word outputs: "Grazie.", "Sì.", "No."…
- Repetition loops: ≤3 unique characters, or unique-word ratio ≤ 0.35

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3.11+-00d4aa?labelColor=0a0f1a&logo=python&logoColor=white)
![macOS](https://img.shields.io/badge/macOS-12+-00d4aa?labelColor=0a0f1a&logo=apple&logoColor=white)
![Apple Silicon](https://img.shields.io/badge/Apple_Silicon-ready-00d4aa?labelColor=0a0f1a)
![rumps](https://img.shields.io/badge/rumps-menubar-00d4aa?labelColor=0a0f1a)

## 🔗 See Also

- [AI Forging Kit](https://github.com/mattiacalastri/AI-Forging-Kit) — the method to forge your AI into a partner
- [EGI — Emergent General Intelligence](https://github.com/mattiacalastri/EGI-Emergent-General-Intelligence) — the theory behind why context beats architecture
- [Polpo Cockpit](https://github.com/mattiacalastri/polpo-cockpit) — orchestrate Claude Code agents from your menubar

## 📄 License

MIT — use it, ship it, build on it.

---

<div align="center">

**Built with 🐙 by [Mattia Calastri](https://mattiacalastri.com) · [Astra Digital Marketing](https://digitalastra.it)**

*"The bottleneck was never the model."*

</div>
