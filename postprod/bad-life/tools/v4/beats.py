#!/usr/bin/env python3
"""BAD LIFE V4 — analyse rythmique de l'audio (attaques + tempo) pour caler les transitions lumineuses.
Usage : beats.py SOURCE DEBUT_S DUREE_S [OUT.json]
Methode : flux spectral (STFT 2048/512 a 48 kHz), pics d'attaque, tempo par autocorrelation.
"""
import json, subprocess, sys
import numpy as np
from scipy.signal import find_peaks, stft
src, ss, dur = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
sr = 48000
raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(ss), '-i', src, '-t', str(dur), '-ac', '1', '-ar', str(sr),
                      '-f', 'f32le', '-'], capture_output=True).stdout
x = np.frombuffer(raw, np.float32)
f, t, Z = stft(x, sr, nperseg=2048, noverlap=2048 - 512)
mag = np.log1p(np.abs(Z) * 100)
flux = np.maximum(np.diff(mag, axis=1), 0).sum(axis=0); ft = t[1:]
flux = (flux - flux.mean()) / (flux.std() + 1e-9)
hop = 512 / sr
pk, _ = find_peaks(flux, height=1.0, distance=int(0.12 / hop))
onsets = ft[pk]
ac = np.correlate(flux, flux, 'full')[len(flux) - 1:]
lags = np.arange(len(ac)) * hop
rng = (lags > 60 / 180) & (lags < 60 / 70)
period = lags[rng][np.argmax(ac[rng])]
res = {'tempo_bpm': round(60 / period, 1), 'periode_s': round(period, 4),
       'attaques_s': [round(float(o), 3) for o in onsets],
       'attaques_fortes_s': [round(float(ft[p]), 3) for p in pk if flux[p] > 2.5]}
print(json.dumps(res, indent=1))
if len(sys.argv) > 4: json.dump(res, open(sys.argv[4], 'w'), indent=1)
