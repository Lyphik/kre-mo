#!/usr/bin/env python3
"""BAD LIFE V5 — detourage du clip entier (etape 3) + indicateurs de fiabilite par image.

- RVM (ONNX) sur l'image ORIGINALE, etat recurrent remis a zero a chaque coupe validee.
- Indicateurs par image : surface personne (alpha > 0,5), part de bord incertain
  (0,1 < alpha < 0,9 rapportee a la surface), instabilite temporelle (|alpha_t - alpha_t-1| moyen
  sur la zone personne, meme plan uniquement).
Sorties : OUT/alpha_%05d.png, OUT/qualite.csv
Usage : matte_full.py SOURCE MODELE.onnx PLANS.csv OUT_DIR [DEBUT_IMG FIN_IMG]
"""
import csv, os, subprocess, sys, time
import numpy as np, onnxruntime as ort, cv2

src, model, plansp, out = sys.argv[1:5]
f0 = int(sys.argv[5]) if len(sys.argv) > 5 else 0
f1 = int(sys.argv[6]) if len(sys.argv) > 6 else None
os.makedirs(out, exist_ok=True)
W, H = 1920, 1080
cuts = {int(r['image_debut']) for r in csv.DictReader(open(plansp))}
sess = ort.InferenceSession(model, providers=['CPUExecutionProvider'])
cmd = ['ffmpeg', '-v', 'error'] + (['-ss', f'{f0 / 50:.3f}'] if f0 else []) + ['-i', src, '-vf', 'scale=in_color_matrix=bt709:in_range=tv,format=rgb24',
       '-f', 'rawvideo', '-']
p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
zero = np.zeros((1, 1, 1, 1), np.float32); ds = np.array([0.25], np.float32)
qname = f'{out}/qualite.csv' if not f0 else f'{out}/qualite_{f0:05d}.csv'   # fenetre : fichier separe (fusion ensuite)
q = open(qname, 'w', newline=''); qw = csv.writer(q); qw.writerow(['image', 'surface', 'bord_incertain', 'instabilite'])
i = f0; prev = None; t0 = time.time(); rec = [zero] * 4
while f1 is None or i < f1:
    buf = p.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    if i in cuts or i == f0: rec = [zero] * 4; prev = None
    x = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32).transpose(2, 0, 1)[None] / 255.0
    fgr, pha, *rec = sess.run(None, {'src': x, 'r1i': rec[0], 'r2i': rec[1], 'r3i': rec[2], 'r4i': rec[3], 'downsample_ratio': ds})
    a = pha[0, 0]
    cv2.imwrite(f'{out}/alpha_{i:05d}.png', np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8))
    surf = float((a > 0.5).mean()); unc = float(((a > 0.1) & (a < 0.9)).mean()) / max(surf, 1e-3)
    ins = float(np.abs(a - prev)[np.maximum(a, prev) > 0.5].mean()) if prev is not None and (np.maximum(a, prev) > 0.5).any() else 0.0
    qw.writerow([i, round(surf, 4), round(unc, 4), round(ins, 4)]); prev = a
    i += 1
    if i % 250 == 0: print(f'{i} images, {(i - f0) / (time.time() - t0):.2f} i/s', flush=True); q.flush()
q.close(); print('TERMINE', i)
