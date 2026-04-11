<p align="center">
  <strong>Jarvis STT</strong>
</p>

<h3 align="center">Voice dictation for Claude Code. Speak. Text appears. Press nothing.</h3>

<p align="center">
  Offline. Instant. No cloud. No subscription. Built for the forge.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-teal.svg" alt="MIT"></a>
  <img src="https://img.shields.io/badge/macOS-Apple%20Silicon-black.svg" alt="Apple Silicon">
  <img src="https://img.shields.io/badge/Whisper-MLX-orange.svg" alt="Whisper MLX">
  <img src="https://img.shields.io/badge/Works%20with-Claude%20Code-white.svg" alt="Claude Code">
</p>

---

## The Problem

Claude Code lives in the terminal. Long prompts break flow. You stop thinking about the problem and start thinking about typing.

The model is ready. Your hands are the bottleneck.

---

## The Solution

Speak your prompt. Jarvis transcribes it offline, pastes it into Claude Code, and hits Return. You never touch the keyboard.

```
Microphone → Whisper MLX → clipboard → Cmd+V → Return
```

Entirely local. Apple Silicon. No API calls. No data leaves your machine.

---

## Features

| Feature | Description |
|---------|-------------|
| **Offline** | Whisper MLX runs entirely on Apple Silicon (M1/M2/M3/M4) |
| **Menu bar** | Live status icon — 🔇 off · 🎙 listening · 🔴 recording · ⚡ transcribing |
| **AutoSend** | Pastes transcription and hits Return automatically |
| **Hallucination filter** | Suppresses Whisper artifacts and repetition loops |
| **Pre-roll buffer** | Captures the first syllable — never clips the start of a word |
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

The 🔇 icon appears in your menu bar. Click → **▶ Avvia**. The icon updates live as you speak. Last transcription is always visible in the menu.

To stop: click the icon → **⏹ Ferma**. No terminal needed.

### Terminal only

```bash
python3 stt.py              # AutoSend ON  (paste + Return)
python3 stt.py --no-send    # paste only, no Return
```

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

## How it works

**VAD (Voice Activity Detection)** is RMS-based — no heavy models, no cloud calls. A pre-roll buffer keeps the last ~200ms of audio before the threshold fires, so the first syllable is always captured.

**Hallucination filter** combines:
- Blacklist patterns (YouTube subtitles, URLs, known Whisper artifacts)
- Unique-word ratio ≤ 0.35 — catches repetition loops like *"renrenrenrenren..."*

**State IPC**: `stt.py` writes state to `~/.local/run/jarvis/stt_state`. `stt_bar.py` polls every second and updates the icon. No sockets, no overhead.

---

## Origin

Built during 800+ sessions of forging an AI-driven operating system with Claude.

The bottleneck was never the model. It was the friction between thought and input. This tool removes that friction.

Part of the [AI Forging Kit](https://github.com/mattiacalastri/AI-Forging-Kit) ecosystem — a framework for building AI into a partner, not a tool.

---

## License

MIT — use it, adapt it, ship it.

---

<p align="center">
  <em>"The bottleneck was never the model."</em>
  <br><br>
  — Mattia Calastri, 2026
</p>
