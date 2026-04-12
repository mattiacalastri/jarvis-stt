#!/usr/bin/env python3
"""
Calibrazione mic Jarvis — mostra RMS in tempo reale.
Esegui, parla, taci, poi leggi i valori per settare la soglia giusta.
"""
import sounddevice as sd
import numpy as np
import time
import sys

DEVICE_RATE = 48000
CHUNK = 1024
DURATION = 30  # secondi di ascolto

print("=== JARVIS MIC CALIBRATION ===")
print(f"Ascolto per {DURATION}s — parla, taci, sussurra, voce normale")
print("Formato: [HH:MM:SS] RMS=X.XXXX  STATO")
print("-" * 50)
sys.stdout.flush()

samples = []
start = time.time()

def cb(indata, frames, time_info, status):
    chunk = indata[:, 0][::3].astype(np.float32)
    rms = float(np.sqrt(np.mean(chunk ** 2)))
    samples.append(rms)
    ts = time.strftime("%H:%M:%S")
    bar = "█" * min(int(rms / 0.005 * 20), 40)
    stato = "SILENZIO" if rms < 0.010 else ("VOCE" if rms < 0.05 else "FORTE")
    print(f"[{ts}] RMS={rms:.5f}  {stato}  |{bar}", flush=True)

with sd.InputStream(samplerate=DEVICE_RATE, channels=1,
                    blocksize=CHUNK, dtype="float32", callback=cb):
    time.sleep(DURATION)

print("-" * 50)
if samples:
    arr = np.array(samples)
    print(f"STATISTICHE {DURATION}s:")
    print(f"  Media:    {arr.mean():.5f}")
    print(f"  Max:      {arr.max():.5f}")
    print(f"  P75:      {np.percentile(arr, 75):.5f}")
    print(f"  P90:      {np.percentile(arr, 90):.5f}")
    print(f"  P99:      {np.percentile(arr, 99):.5f}")
    print(f"")
    noise_floor = np.percentile(arr, 30)
    suggested = max(0.012, noise_floor * 5)
    print(f"  Noise floor (P30): {noise_floor:.5f}")
    print(f"  SOGLIA CONSIGLIATA: {suggested:.5f}")
