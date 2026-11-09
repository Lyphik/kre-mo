#!/usr/bin/env python3
"""Mesure de derive des tons de peau : compare des patchs (zones de peau choisies a la main)
entre l'image source et des images etalonnees. Sortie : luma Y', chroma, teinte (deg, vectorscope).
Usage : skin_probe.py patches.json   (voir docs/04-controle-qualite.md)
"""
import json, sys, math
import numpy as np
from PIL import Image, ImageDraw

def stats(img, box):
    x, y, w, h = box
    a = np.asarray(img.convert('RGB'), dtype=np.float64)[y:y + h, x:x + w] / 255.0
    r, g, b = a[..., 0].mean(), a[..., 1].mean(), a[..., 2].mean()
    Y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    cb, cr = (b - Y) / 1.8556, (r - Y) / 1.5748
    return Y, math.hypot(cb, cr), math.degrees(math.atan2(cr, cb)) % 360

cfg = json.load(open(sys.argv[1]))
for shot in cfg['shots']:
    imgs = {k: Image.open(v) for k, v in shot['images'].items()}
    for i, box in enumerate(shot['boxes']):
        ref = stats(imgs['source'], box)
        line = [f"{shot['name']} patch{i}"]
        for k, im in imgs.items():
            Y, c, h = stats(im, box)
            line.append(f"{k}: Y={Y:.3f} C={c:.3f} H={h:5.1f}" + ("" if k == 'source' else f" (dH={((h - ref[2] + 180) % 360) - 180:+.1f})"))
        print(' | '.join(line))
    if cfg.get('annotate'):
        im = imgs['source'].convert('RGB').copy(); d = ImageDraw.Draw(im)
        for x, y, w, h in shot['boxes']:
            d.rectangle([x, y, x + w, y + h], outline=(255, 255, 0), width=3)
        im.save(cfg['annotate'].replace('.jpg', f"_{shot['name']}.jpg"))
