#!/usr/bin/env python3
"""BAD LIFE V5.1 — les effets ameliorent-ils les plans ? Mesures sur le DECOR (alpha < 0,05), aux images
cles de profondeur, entre : etalonnage seul (reference), V5 et V5.1.

  effets      : energie ajoutee par les effets = moyenne |X - etalonnage| (quantite de VFX)
  detail_proche / detail_loin : micro-contraste (|Laplacien|) du decor proche (disparite > 0,6) / lointain
                (< 0,3), rapporte a l'etalonnage seul (1,00 = aucun detail perdu)
  noirs       : 2e percentile de luminance du decor (voile = noirs releves)
  separation  : rapport micro-contraste proche / lointain (perspective atmospherique lisible)
Usage : metrics_v51.py EXTRAITS.json ID ETAL.mp4 V5.mp4 V51.mp4 MATTE_DIR DEPTH_DIR
"""
import json, os, subprocess, sys
import numpy as np, cv2

EXTP, EID, ETAL, V5, V51, MATTE, DEPTH = sys.argv[1:8]
ex = next(e for e in json.load(open(EXTP))['extraits'] if e['id'] == EID)
F0, F1 = int(round(ex['debut_s'] * 50)), int(round(ex['fin_s'] * 50))
W, H = 960, 540


def frames(p):
    b = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', p, '-vf', f'scale={W}:{H}:flags=area,format=rgb48le', '-f', 'rawvideo', '-'],
                       capture_output=True).stdout
    return np.frombuffer(b, np.uint16).reshape(-1, H, W, 3)


E, A, B = frames(ETAL), frames(V5), frames(V51)
keys = sorted(int(f[6:11]) for f in os.listdir(DEPTH) if f.startswith('depth_') and F0 <= int(f[6:11]) < F1)
acc = {k: [] for k in ('eff5', 'eff51', 'dp5', 'dp51', 'dl5', 'dl51', 'n_e', 'n_5', 'n_51', 'sep_e', 'sep_5', 'sep_51')}
L = lambda im: (im[..., 0] * 0.2126 + im[..., 1] * 0.7152 + im[..., 2] * 0.0722) / 65535
lap = lambda y: np.abs(cv2.Laplacian(y.astype(np.float32), cv2.CV_32F, ksize=3))
for k in keys:
    n = k - F0
    if n >= min(len(E), len(A), len(B)): break
    al = cv2.resize(cv2.imread(f'{MATTE}/alpha_{k:05d}.png', 0), (W, H)) / 255.0
    d = cv2.resize(cv2.imread(f'{DEPTH}/depth_{k:05d}.png', -1).astype(np.float32) / 65535, (W, H))
    dec = al < 0.05; near = dec & (d > 0.6); far = dec & (d < 0.3)
    if dec.sum() < 1000: continue
    le, l5, l51 = L(E[n]), L(A[n]), L(B[n])
    acc['eff5'].append(np.abs(l5 - le)[dec].mean()); acc['eff51'].append(np.abs(l51 - le)[dec].mean())
    ge, g5, g51 = lap(le), lap(l5), lap(l51)
    if near.sum() > 500:
        acc['dp5'].append(g5[near].mean() / (ge[near].mean() + 1e-6)); acc['dp51'].append(g51[near].mean() / (ge[near].mean() + 1e-6))
    if far.sum() > 500:
        acc['dl5'].append(g5[far].mean() / (ge[far].mean() + 1e-6)); acc['dl51'].append(g51[far].mean() / (ge[far].mean() + 1e-6))
    if near.sum() > 500 and far.sum() > 500:
        for t, g in (('e', ge), ('5', g5), ('51', g51)): acc['sep_' + t].append(g[near].mean() / (g[far].mean() + 1e-6))
    for t, y in (('e', le), ('5', l5), ('51', l51)): acc['n_' + t].append(np.percentile(y[dec], 2))
m = {k: (float(np.mean(v)) if v else None) for k, v in acc.items()}
f = lambda x, p=3: '—' if x is None else f'{x:.{p}f}'
res = dict(extrait=EID, images_mesurees=len(acc['eff5']),
           effets_V5=f(m['eff5'], 4), effets_V51=f(m['eff51'], 4),
           detail_proche_V5=f(m['dp5']), detail_proche_V51=f(m['dp51']),
           detail_loin_V5=f(m['dl5']), detail_loin_V51=f(m['dl51']),
           noirs_etalonnage=f(m['n_e'], 4), noirs_V5=f(m['n_5'], 4), noirs_V51=f(m['n_51'], 4),
           separation_etalonnage=f(m['sep_e'], 2), separation_V5=f(m['sep_5'], 2), separation_V51=f(m['sep_51'], 2))
print(json.dumps(res, ensure_ascii=False))
