<p align="center">
  <strong>Jarvis STT</strong>
</p>

<h3 align="center">Voice dictation for Claude Code. Speak. Text appears. Press nothing.</h3>

<p align="center">
  Offline. Instant. No cloud. No subscription. Built in the forge.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-teal.svg" alt="MIT"></a>
  <img src="https://img.shields.io/badge/macOS-Apple%20Silicon-black.svg" alt="Apple Silicon">
  <img src="https://img.shields.io/badge/Whisper-MLX-orange.svg" alt="Whisper MLX">
  <img src="https://img.shields.io/badge/Works%20with-Claude%20Code-white.svg" alt="Claude Code">
  <img src="https://img.shields.io/badge/Sessions-874%2B-white.svg" alt="874+ Sessions">
</p>

---

## The Problem

Claude Code lives in the terminal. Long prompts break flow.

You stop thinking about the problem and start thinking about typing. The model is ready. The model has been ready. **Your hands are the bottleneck.**

Every word you type is a word you didn't think.

---

## The Solution

Speak your prompt. Jarvis transcribes it offline, pastes it into Claude Code, and hits Return. The thought goes directly to the model. Nothing in between.

```
Microphone → Whisper MLX (Apple Silicon) → clipboard → Cmd+V → Return
```

Entirely local. No API calls. No data leaves your machine. No latency waiting for a server you don't control.

---

## Origin

This tool was extracted from 874 sessions of building an AI-driven operating system with Claude.

At some point the friction was no longer the model — it was the distance between thought and input. Voice removed that distance. This is the distillation of what worked.

It's the first step toward something larger: a system that understands when you're talking *to* it — not just transcribing everything you say. That's `vocative-detect`, still in the forge. This is the foundation.

Part of the [9 Open Source Tools](https://github.com/mattiacalastri/AI-Forging-Kit) emerging from the forge.

---

## Features

| Feature | Description |
|---------|-------------|
| **Offline** | Whisper MLX runs entirely on Apple Silicon (M1/M2/M3/M4) |
| **Menu bar** | Live status icon — 🔇 off · 🎙 listening · 🔴 recording · ⚡ transcribing |
| **AutoSend** | Pastes transcription and hits Return automatically |
| **Hallucination filter** | Suppresses Whisper artifacts and repetition loops |
| **Pre-roll buffer** | Never clips the first syllable |
| **One-click stop** | No hunting for a terminal to kill the process |

---

## Requirements

- macOS with Apple Silicon (M1 or later)
- Python 3.11+
- Microphone access

---

## Installation

```bash
git clone https://github.com/mattiacalastri/jarvis-stt.git
cd jarvis-stt
pip3 install -r requirements.txt
```

First run downloads the Whisper model (~500MB, cached locally after that).

---

## Usage

### Menu bar (recommended)

```bash
python3 stt_bar.py
```

🔇 in your menu bar. Click → **▶ Avvia**. Icon updates live. Last transcription visible in the menu. Stop with one click — no terminal needed.

### Terminal only

```bash
python3 stt.py              # AutoSend ON  (paste + Return)
python3 stt.py --no-send    # paste only, no Return
```

---

## How it works

**VAD** is RMS-based — no heavy models, no cloud calls. A 200ms pre-roll buffer captures audio before the threshold fires, so the first syllable is always in the recording.

**Hallucination filter** combines blacklist patterns (YouTube subtitles, URLs, known artifacts) with a unique-word ratio check — catches repetition loops like *"renrenrenrenren..."* before they reach your cursor.

**State IPC**: `stt.py` writes to `~/.local/run/jarvis/stt_state`. `stt_bar.py` polls every second. No sockets, no overhead, no daemon.

---

## Configuration

Edit the constants at the top of `stt.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL` | `whisper-small-mlx` | Whisper model size |
| `LANG` | `it` | Language (`it`, `en`, `auto`) |
| `THRESHOLD` | `0.004` | RMS speech detection threshold |
| `SILENCE` | `1.5` | Seconds of silence to end an utterance |
| `MAX_DUR` | `12.0` | Maximum utterance duration (seconds) |

### Model options

| Model | Quality | Latency |
|-------|---------|---------|
| `whisper-tiny-mlx` | ⭐⭐ | ~0.07s |
| `whisper-base-mlx` | ⭐⭐⭐ | ~0.15s |
| `whisper-small-mlx` | ⭐⭐⭐⭐ | ~0.4s ← recommended |
| `whisper-medium-mlx` | ⭐⭐⭐⭐⭐ | ~1.5s |

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
