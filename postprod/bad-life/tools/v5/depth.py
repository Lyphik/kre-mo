#!/usr/bin/env python3
"""BAD LIFE V5 — profondeur du decor (Depth Anything V2 Small, ONNX, Apache-2.0).

Usage du resultat : densite de brume selon la perspective, occultation des particules par le decor
proche. JAMAIS applique aux artistes (ils sont recomposes depuis la source).
- Calcul 1 image sur STEP (defaut 4), sortie 'disparite' normalisee PAR PLAN (percentiles 2-98 du
  plan entier) pour eviter les sauts d'echelle, puis interpolation temporelle a la lecture.
Sortie : OUT/depth_%05d.png (16 bits, 480x270, 0 = loin, 65535 = proche), seulement images cles.
Usage : depth.py SOURCE MODELE.onnx PLANS.csv EXTRAITS.json OUT_DIR [STEP]
"""
import csv, json, os, subprocess, sys
import numpy as np, onnxruntime as ort, cv2

src, model, plansp, extp, out = sys.argv[1:6]
STEP = int(sys.argv[6]) if len(sys.argv) > 6 else 4
os.makedirs(out, exist_ok=True)
plans = [(int(r['image_debut']), int(r['image_fin'])) for r in csv.DictReader(open(plansp))]
so = ort.SessionOptions(); so.intra_op_num_threads = 4
sess = ort.InferenceSession(model, so, providers=['CPUExecutionProvider']); iname = sess.get_inputs()[0].name
for ex in json.load(open(extp))['extraits']:
    a, b = int(round(ex['debut_s'] * 50)), int(round(ex['fin_s'] * 50))
    # images cles : 1 sur STEP + premiere et derniere image de chaque plan
    keys = set(range(a, b, STEP))
    for p0, p1 in plans:
        if p1 > a and p0 < b: keys.update([max(p0, a), min(p1, b) - 1])
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{a / 50:.3f}', '-i', src, '-t', f'{(b - a) / 50:.3f}', '-vf',
                          'scale=518:518:flags=area,format=rgb24', '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
    raw = {}
    for i in range(a, b):
        buf = p.stdout.read(518 * 518 * 3)
        if len(buf) < 518 * 518 * 3: break
        if i not in keys: continue
        x = np.frombuffer(buf, np.uint8).reshape(518, 518, 3).astype(np.float32) / 255
        x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).transpose(2, 0, 1)[None].astype(np.float32)
        raw[i] = cv2.resize(sess.run(None, {iname: x})[0].squeeze(), (480, 270), interpolation=cv2.INTER_AREA)
    for p0, p1 in plans:                               # normalisation par plan
        ks = [k for k in raw if p0 <= k < p1]
        if not ks: continue
        allv = np.concatenate([raw[k].ravel() for k in ks])
        lo, hi = np.percentile(allv, 2), np.percentile(allv, 98)
        for k in ks:
            d = np.clip((raw[k] - lo) / (hi - lo + 1e-6), 0, 1)
            cv2.imwrite(f'{out}/depth_{k:05d}.png', (d * 65535).astype(np.uint16))
    print(ex['id'], len(raw), 'images cles', flush=True)
