#!/usr/bin/env python3
"""BAD LIFE V5 — analyse musicale complete (etape 2 / section 7 du cahier des charges).

Mesures (audio mono 22,05 kHz, STFT 2048 / pas 256) :
  kicks  : flux spectral 40-120 Hz, pics ;      snares : flux spectral 1,5-8 kHz, pics ;
  basses : energie RMS 40-200 Hz ;              energie globale (RMS, lissee 1 s) ;
  tempo  : autocorrelation de l'enveloppe d'attaques (70-180 BPM) + phase calee sur les kicks ;
  sections : spectrogramme log-mel moyenne par temps -> matrice d'auto-similarite -> nouveaute
             (noyau en damier de 16 temps) -> frontieres ; etiquetage des repetitions (A, B, C...)
             et du niveau d'energie (refrain presume = section repetee la plus energique).
  impacts : instants combinant kick + snare + saut d'energie (les plus forts).
Sorties : OUT.json, OUT.png (frise : energie, basses, kicks, snares, sections, coupes du montage).
Usage : music.py SOURCE PLANS.csv OUT_PREFIX
"""
import csv, json, subprocess, sys
import numpy as np
from scipy.signal import find_peaks, stft
from scipy.ndimage import uniform_filter1d

src, plansp, outp = sys.argv[1:4]
sr = 22050
x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'],
                                 capture_output=True).stdout, np.float32)
dur = len(x) / sr
f, t, Z = stft(x, sr, nperseg=2048, noverlap=2048 - 256)
P = np.abs(Z) ** 2; hop = 256 / sr


def band_flux(lo, hi):
    m = (f >= lo) & (f < hi)
    lb = np.log1p(P[m] * 1e4)
    fl = np.maximum(np.diff(lb, axis=1), 0).sum(axis=0)
    fl = np.concatenate([[0], fl])
    return (fl - np.median(fl)) / (np.percentile(fl, 95) - np.median(fl) + 1e-9)


kick_env = band_flux(40, 120); snare_env = band_flux(1500, 8000); full_env = band_flux(30, 11000)
bass = np.sqrt(P[(f >= 40) & (f < 200)].sum(axis=0)); bass = bass / (bass.max() + 1e-9)
rms = np.sqrt(P.sum(axis=0)); energy = uniform_filter1d(rms, int(1.0 / hop)); energy /= energy.max()
kicks = t[find_peaks(kick_env, height=0.9, distance=int(0.2 / hop))[0]]
snares = t[find_peaks(snare_env, height=1.0, distance=int(0.2 / hop))[0]]
# tempo
# Autocorrelation + filtre en PEIGNE : la periode retenue est celle dont les 8 premiers multiples
# (temps, demi-mesure, mesure, 2 mesures) sont les plus correles. Un simple maximum confondait le
# tempo (~100 BPM, mesure de 2,40 s) avec la syncope '3-3-2' des kicks (3 doubles croches = 132 BPM).
ac = np.correlate(full_env - full_env.mean(), full_env - full_env.mean(), 'full')[len(full_env) - 1:]
ac = ac / ac[0]; lags = np.arange(len(ac)) * hop
cands = np.arange(60 / 180, 60 / 70, hop)
comb = [np.mean([np.interp(k * pp, lags, ac) for k in range(1, 9)]) for pp in cands]
period = float(cands[int(np.argmax(comb))])
# affinage local sur le pic d'autocorrelation le plus proche
loc = (lags > period * 0.97) & (lags < period * 1.03)
period = float(lags[loc][np.argmax(ac[loc])]) if loc.any() else period
bpm = 60 / period
alt = sorted(((float(c), float(v)) for c, v in zip(cands, comb)), key=lambda z: -z[1])[:1]
# phase de la grille : maximise la somme des kicks sur la grille
phases = np.linspace(0, period, 64, endpoint=False)
score = [np.sum(np.interp(np.arange(ph, dur, period), t, np.maximum(kick_env, 0))) for ph in phases]
beats = np.arange(phases[int(np.argmax(score))], dur, period)
# sections : log-mel moyenne par temps
nm = 48; mel = lambda hz: 2595 * np.log10(1 + hz / 700)
edges = 700 * (10 ** (np.linspace(mel(40), mel(10000), nm + 2) / 2595) - 1)
M = np.stack([P[(f >= edges[k]) & (f < edges[k + 2])].sum(axis=0) for k in range(nm)])
L = np.log1p(M * 1e3)
bidx = np.searchsorted(t, beats)
Bf = np.stack([L[:, bidx[k]:bidx[k + 1]].mean(axis=1) if bidx[k + 1] > bidx[k] else L[:, bidx[k]] for k in range(len(bidx) - 1)], axis=1)
Bn = (Bf - Bf.mean(axis=1, keepdims=True)); Bn /= (np.linalg.norm(Bn, axis=0, keepdims=True) + 1e-9)
SSM = Bn.T @ Bn
K = 16; ker = np.outer(np.r_[-np.ones(K), np.ones(K)], np.r_[-np.ones(K), np.ones(K)])
g = np.exp(-0.5 * (np.linspace(-2, 2, 2 * K) ** 2)); ker *= np.outer(g, g)
nov = np.zeros(SSM.shape[0])
for i in range(K, SSM.shape[0] - K):
    nov[i] = (SSM[i - K:i + K, i - K:i + K] * ker).sum()
nov = np.maximum(nov, 0); nov /= nov.max() + 1e-9
bnd = find_peaks(nov, height=0.25, distance=8)[0]
bt = [0.0] + [float(beats[b]) for b in bnd] + [dur]
secs = []
for k in range(len(bt) - 1):
    a, b = np.searchsorted(beats, bt[k]), max(np.searchsorted(beats, bt[k + 1]) - 1, np.searchsorted(beats, bt[k]) + 1)
    feat = Bf[:, a:min(b, Bf.shape[1])].mean(axis=1)
    e = float(np.mean(np.interp(np.linspace(bt[k], bt[k + 1], 50), t, energy)))
    secs.append(dict(debut_s=round(bt[k], 2), fin_s=round(bt[k + 1], 2), energie=round(e, 3), feat=feat))
# etiquettes de repetition
labels = []; protos = []
for s in secs:
    v = s['feat'] - s['feat'].mean(); v /= np.linalg.norm(v) + 1e-9
    sims = [float(v @ p) for p in protos]
    if sims and max(sims) > 0.95:
        labels.append(chr(65 + int(np.argmax(sims))))
    else:
        protos.append(v); labels.append(chr(65 + len(protos) - 1))
for s, l in zip(secs, labels): s['etiquette'] = l; del s['feat']
# Pas d'etiquette 'refrain' affirmee : dans ce morceau la meme boucle instrumentale tourne du debut a
# la fin, le timbre ne separe pas couplet / refrain. On classe par INTENSITE mesuree ; les sections
# 'forte' sont les candidates refrain, A CONFIRMER par l'artiste.
chorus = None
for s in secs:
    s['intensite'] = 'forte' if s['energie'] >= 0.68 else ('moyenne' if s['energie'] >= 0.50 else 'calme')
# impacts : kick ET snare (+/- 40 ms) et/ou frontiere de section, ponderes par saut d'energie
imp = []
for k in kicks:
    sn = snares[np.abs(snares - k) < 0.04]
    jump = float(np.interp(k + 0.3, t, energy) - np.interp(k - 0.6, t, energy))
    sc = float(np.interp(k, t, kick_env)) + (float(np.interp(sn[0], t, snare_env)) if len(sn) else 0) + 8 * max(jump, 0)
    imp.append((sc, float(k)))
imp.sort(reverse=True)
impacts = sorted(round(k, 3) for _, k in imp[:40])
cuts = [float(r['debut_s']) for r in csv.DictReader(open(plansp)) if float(r['debut_s']) > 0]
on_beat = [c for c in cuts if np.min(np.abs(beats - c)) < 0.06]
res = dict(duree_s=round(dur, 2), tempo_bpm=round(bpm, 2), periode_s=round(period, 4), nb_temps=len(beats),
           temps_s=[round(float(b), 3) for b in beats], kicks_s=[round(float(k), 3) for k in kicks],
           snares_s=[round(float(s), 3) for s in snares], sections=secs,
           impacts_s=impacts, coupes_sur_temps=f'{len(on_beat)}/{len(cuts)} coupes a moins de 60 ms d\'un temps')
json.dump(res, open(outp + '.json', 'w'), indent=1)
print(f"tempo {bpm:.2f} BPM | {len(kicks)} kicks | {len(snares)} snares | {len(secs)} sections | {res['coupes_sur_temps']}")
for s in secs: print(f"  {s['debut_s']:7.2f}-{s['fin_s']:7.2f} s  timbre {s['etiquette']}  energie {s['energie']:.2f}  {s['intensite']}")
# frise
try:
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(4, 1, figsize=(18, 7), sharex=True, gridspec_kw=dict(height_ratios=[2, 1, 1, 1]))
    ax[0].plot(t, energy, color='#c0392b', lw=1, label='energie'); ax[0].plot(t, uniform_filter1d(bass, int(0.5 / hop)), color='#2c3e50', lw=0.8, label='basses')
    cols = {'A': '#d6eaf8', 'B': '#fadbd8', 'C': '#d5f5e3', 'D': '#fcf3cf', 'E': '#e8daef', 'F': '#f6ddcc', 'G': '#d0ece7'}
    for s in secs:
        ax[0].axvspan(s['debut_s'], s['fin_s'], color={'forte': '#fadbd8', 'moyenne': '#fcf3cf', 'calme': '#d6eaf8'}[s['intensite']], alpha=0.7)
        ax[0].text((s['debut_s'] + s['fin_s']) / 2, 1.02, s['intensite'], ha='center', fontsize=7)
    ax[0].legend(loc='lower right', fontsize=7); ax[0].set_ylim(0, 1.12); ax[0].set_ylabel('niveau')
    ax[1].vlines(kicks, 0, 1, color='#2c3e50', lw=0.6); ax[1].set_ylabel('kicks')
    ax[2].vlines(snares, 0, 1, color='#e67e22', lw=0.6); ax[2].vlines(impacts, 0, 1, color='#c0392b', lw=1.6); ax[2].set_ylabel('snares /\nimpacts')
    ax[3].vlines(cuts, 0, 1, color='#7f8c8d', lw=0.5); ax[3].set_ylabel('coupes'); ax[3].set_xlabel('temps (s)')
    for a in ax: a.set_yticks([])
    plt.tight_layout(); plt.savefig(outp + '.png', dpi=110)
except ImportError:
    print('matplotlib absent : pas de frise')
