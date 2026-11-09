#!/usr/bin/env python3
"""BAD LIFE V4 — detourage des personnes (Robust Video Matting, ONNX, CPU).

Le matte sert UNIQUEMENT de masque : il protege les artistes (effets places derriere eux,
etalonnage 'sujets' distinct du 'decor'). Les pixels des artistes ne sont jamais generes ni
modifies par l'IA.

- Entree : image source originale (non etalonnee), 1080p.
- Etat recurrent RVM remis a zero a chaque coupe (pas de 'fuite' d'un plan sur l'autre).
- Sortie : alpha 8 bits par image (PNG), dossier OUT/alpha_%05d.png

Usage : matte.py SOURCE MODELE.onnx CONFIG.json OUT_DIR
Modele : rvm_mobilenetv3_fp32.onnx, release v1.0.0 de PeterL1n/RobustVideoMatting (GPL-3.0).
"""
import json, subprocess, sys, os, time
import numpy as np, onnxruntime as ort, cv2

src, model, cfgp, out = sys.argv[1:5]
cfg = json.load(open(cfgp)); os.makedirs(out, exist_ok=True)
W, H = 1920, 1080
cuts = {s['f0'] for s in cfg['shots']}
sess = ort.InferenceSession(model, providers=['CPUExecutionProvider'])
cmd = ['ffmpeg', '-v', 'error', '-ss', str(cfg['source_start_s']), '-i', src, '-t', str(cfg['duration_s']),
       '-vf', 'scale=in_color_matrix=bt709:in_range=tv,format=rgb24', '-f', 'rawvideo', '-']
p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
zero = np.zeros((1, 1, 1, 1), np.float32); ds = np.array([0.25], np.float32)
i = 0; t0 = time.time()
while True:
    buf = p.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    if i in cuts: rec = [zero] * 4
    x = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32).transpose(2, 0, 1)[None] / 255.0
    fgr, pha, *rec = sess.run(None, {'src': x, 'r1i': rec[0], 'r2i': rec[1], 'r3i': rec[2], 'r4i': rec[3], 'downsample_ratio': ds})
    cv2.imwrite(f'{out}/alpha_{i:05d}.png', np.clip(pha[0, 0] * 255 + 0.5, 0, 255).astype(np.uint8))
    i += 1
    if i % 50 == 0: print(f'{i} images, {i / (time.time() - t0):.2f} i/s', flush=True)
print(f'TERMINE {i} images')
