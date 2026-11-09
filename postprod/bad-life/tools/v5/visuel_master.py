#!/usr/bin/env python3
"""BAD LIFE V5.1 — planches d'inspection visuelle du master.

  planche_plans_NN.jpg   : pour chaque plan reel (>= 0,3 s), image du milieu SOURCE | MASTER (reduites).
  zones_protegees_NN.jpg : recadrage 100 % (pixels 4K) de la zone artistes la plus grande de plans choisis,
                           SOURCE agrandie (Lanczos) | MASTER | difference x8 (hors zone protegee grisee).
  transitions.jpg        : chaque transition musicale a t-0,10 / t / t+0,04 / t+0,10 / t+0,20 s, SOURCE et MASTER.
Usage : visuel_master.py SOURCE MASTER.mp4 PLANS.csv MATTE_DIR TRANSITIONS_S(json list) OUT_DIR [N_ZONES=10]
"""
import csv, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

SRC, MST, PLANS, MATTE, TRJ, OUT = sys.argv[1:7]
NZ = int(sys.argv[7]) if len(sys.argv) > 7 else 10
FPS = 50.0
os.makedirs(OUT, exist_ok=True)


def grab(path, idx, w=None):
    """Image d'indice idx (seek precis), RGB uint8 ; redimensionnee en largeur w si demande."""
    vf = [f'select=eq(n\\,{idx % 50})']
    if w: vf.append(f'scale={w}:-2:flags=lanczos')
    vf.append('format=rgb24')
    t0 = (idx // 50)                                   # seek a la seconde entiere puis selection exacte
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', str(t0), '-i', path, '-vf', ','.join(vf),
                        '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True)
    from io import BytesIO
    return Image.open(BytesIO(r.stdout)).convert('RGB')


def label(im, txt):
    d = ImageDraw.Draw(im); d.rectangle([0, 0, 8 + 7 * len(txt), 16], fill=(0, 0, 0)); d.text((4, 3), txt, fill=(255, 255, 255))
    return im


plans = [r for r in csv.DictReader(open(PLANS)) if float(r['duree_s']) >= 0.3 and not r['famille'].startswith('X')]

# 1. planches par plan
TW = 320; TH = 180; COLS = 4; ROWS = 8
per = COLS * ROWS
for s in range(0, len(plans), per):
    sheet = Image.new('RGB', (COLS * (2 * TW + 12), ROWS * (TH + 4)), (24, 24, 24))
    for k, p in enumerate(plans[s:s + per]):
        mid = (int(p['image_debut']) + int(p['image_fin'])) // 2
        a = label(grab(SRC, mid, TW), f"P{p['plan']} {mid / FPS:.2f}s src")
        b = label(grab(MST, mid, TW), f"{p['famille'][:14]} master")
        x = (k % COLS) * (2 * TW + 12); y = (k // COLS) * (TH + 4)
        sheet.paste(a, (x, y)); sheet.paste(b, (x + TW + 2, y))
    sheet.save(f'{OUT}/planche_plans_{s // per + 1:02d}.jpg', quality=88)
    print('planche', s // per + 1)

# 2. zones protegees a 100 % : plans reels repartis sur les familles, image avec la plus grande surface artistes
byfam = {}
for p in plans: byfam.setdefault(p['famille'], []).append(p)
choix = []
while len(choix) < NZ and any(byfam.values()):
    for f in sorted(byfam):
        if byfam[f] and len(choix) < NZ:
            lst = byfam[f]; choix.append(lst.pop(len(lst) // 2))
CW, CH = 960, 540
for n, p in enumerate(choix):
    i0, i1 = int(p['image_debut']), int(p['image_fin'])
    best, bi = -1, i0
    for i in range(i0, i1, max(1, (i1 - i0) // 8)):
        a = np.asarray(Image.open(f'{MATTE}/alpha_{i:05d}.png'), np.float32) / 255
        if a.sum() > best: best, bi = a.sum(), i
    al = np.asarray(Image.open(f'{MATTE}/alpha_{bi:05d}.png').resize((3840, 2160), Image.BILINEAR), np.float32) / 255
    ys, xs = np.nonzero(al > 0.97)
    if len(ys) == 0: continue
    cy = int(np.percentile(ys, 15)) + CH // 3; cx = int(np.median(xs))     # haut de la silhouette (visage, buste)
    x0 = int(np.clip(cx - CW // 2, 0, 3840 - CW)); y0 = int(np.clip(cy - CH // 2, 0, 2160 - CH))
    s4 = np.asarray(grab(SRC, bi, 3840), np.int16)[y0:y0 + CH, x0:x0 + CW]
    m4 = np.asarray(grab(MST, bi), np.int16)[y0:y0 + CH, x0:x0 + CW]
    a4 = al[y0:y0 + CH, x0:x0 + CW]
    diff = np.clip(np.abs(m4 - s4).max(axis=2) * 8, 0, 255).astype(np.uint8)
    dv = np.stack([diff] * 3, -1); dv[a4 < 0.97] = (dv[a4 < 0.97] * 0.25 + 40).astype(np.uint8)
    im = Image.new('RGB', (3 * CW + 8, CH), (0, 0, 0))
    im.paste(label(Image.fromarray(s4.astype(np.uint8)), f"P{p['plan']} {bi / FPS:.2f}s SOURCE (Lanczos)"), (0, 0))
    im.paste(label(Image.fromarray(m4.astype(np.uint8)), f"{p['famille']} MASTER 100%"), (CW + 4, 0))
    im.paste(label(Image.fromarray(dv), 'ecart x8 (gris = hors zone protegee)'), (2 * CW + 8, 0))
    im.save(f'{OUT}/zones_protegees_{n + 1:02d}.jpg', quality=90)
    print('zone', n + 1, p['famille'], bi)

# 3. transitions
trs = json.loads(TRJ)
offs = [-0.10, 0.0, 0.04, 0.10, 0.20]
W2 = 384; H2 = 216
im = Image.new('RGB', (len(offs) * (W2 + 2), len(trs) * (2 * H2 + 10)), (24, 24, 24))
for r, t in enumerate(trs):
    for c, o in enumerate(offs):
        idx = int(round((t + o) * FPS))
        im.paste(label(grab(SRC, idx, W2), f'{t:.2f}{o:+.2f}s src'), (c * (W2 + 2), r * (2 * H2 + 10)))
        im.paste(label(grab(MST, idx, W2), 'master'), (c * (W2 + 2), r * (2 * H2 + 10) + H2 + 2))
im.save(f'{OUT}/transitions.jpg', quality=88)
print('TERMINE')
