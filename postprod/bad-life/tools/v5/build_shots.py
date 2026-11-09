#!/usr/bin/env python3
"""BAD LIFE V5 — table des plans reels + pre-classement par ambiance + passages N&B (etape 2).

Entrees : candidats (detect_cuts.py), validation visuelle (data/v5/cuts_validation.json).
Mesures par image (decodage 160x90) : luminance, saturation, parts de rouge / vert / beige.
Sorties : data/v5/plans.csv (segments), data/v5/nb_images.json (passages N&B image par image).
La famille est un PRE-classement automatique, a verifier sur planche (overrides possibles dans
data/v5/familles_overrides.json).
Usage : build_shots.py SOURCE CANDIDATS.json VALIDATION.json OVERRIDES.json OUT_DIR
"""
import csv, json, os, subprocess, sys
import numpy as np, cv2

src, candp, valp, ovp, out = sys.argv[1:6]
cand = json.load(open(candp))['candidats']; val = json.load(open(valp))
ov = json.load(open(ovp)) if os.path.exists(ovp) else {}
rej = {int(k) for k in val['rejetes'] if k.isdigit()}
W, H, FPS = 160, 90, 50.0
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-vf', f'scale={W}:{H}:flags=area,format=yuv444p',
                      '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
F = []
while True:
    b = p.stdout.read(W * H * 3)
    if len(b) < W * H * 3: break
    yuv = np.frombuffer(b, np.uint8).reshape(3, H, W)
    Yp, Up, Vp = (c.astype(np.float32) for c in yuv)
    mid = (Yp > 40) & (Yp < 220)
    chroma = float(np.hypot(Up - 128, Vp - 128)[mid].mean()) if mid.mean() > 0.30 else float('nan')
    im = cv2.cvtColor(np.ascontiguousarray(yuv.transpose(1, 2, 0)), cv2.COLOR_YUV2BGR)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); h, s, v = hsv[..., 0], hsv[..., 1].astype(np.float32), hsv[..., 2]
    col = (s > 70) & (v > 35)
    hist = cv2.normalize(cv2.calcHist([hsv], [0, 1], None, [16, 8], [0, 180, 0, 256]), None).flatten()
    F.append(dict(hist=hist, y=float(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).mean()), s=float(s.mean()), chroma=chroma,
                  rouge=float((col & ((h < 9) | (h > 165))).mean()), vert=float((col & (h > 35) & (h < 95)).mean()),
                  beige=float(((s > 25) & (s < 110) & (h >= 10) & (h <= 30) & (v > 90)).mean())))
n = len(F)
y = np.array([f['y'] for f in F]); sat = np.array([f['s'] for f in F])

# N&B image par image : chrominance YUV moyenne des tons moyens (Y 40-220). Calibration sur images
# connues : N&B 1,8-2,0 ; couleur meme tres desaturee >= 4,0. Seuil 3,0. Si moins de 30 % de tons
# moyens (nuit tres sombre, fondu au noir) : indetermine -> non classe N&B.
chroma = np.array([f['chroma'] for f in F])
nb = np.nan_to_num(chroma, nan=99) < 3.0
# frontieres de plans : coupes validees ; les flashs delimitent un micro-segment 'flash'
cuts = sorted({c['image'] for c in cand if c['image'] not in rej})
kinds = {c['image']: c['type'] for c in cand}
zones = val['effets_de_montage']['zones_s']; fin = val['fondu_de_fin_s']
bounds = [0] + cuts + [n]
rows = []
for k in range(len(bounds) - 1):
    a, b = bounds[k], bounds[k + 1]
    if b <= a: continue
    seg = F[a:b]; med = lambda key: float(np.median([f[key] for f in seg]))
    yy, ss, rr, vv, bb = med('y'), med('s'), med('rouge'), med('vert'), med('beige')
    nbfrac = float(nb[a:b].mean()); dur = (b - a) / FPS
    tm = (a + b) / 2 / FPS
    if any(z0 <= tm <= z1 for z0, z1 in zones) or kinds.get(a) == 'flash' or (b - a) == 1:
        fam = 'X_effet_montage'                        # salves, flashs et inserts d'une seule image
    elif fin[0] <= a / FPS:
        fam = 'OUTRO_fondu'
    elif nbfrac > 0.6:
        fam = 'NB'
    elif rr > 0.12 and yy < 110:
        fam = 'B_nuit_rouge'
    elif yy < 55:
        fam = 'D_nuit_exterieure'
    elif bb > 0.18:
        fam = 'C_rideau_metallique'
    else:
        fam = 'A_jour_cite'
    # correction manuelle : cle = image de debut, tolerance +/- 2 images (une nouvelle coupe ou un
    # insert peut decaler le debut d'une image) ; jamais appliquee a un insert d'une image.
    if (b - a) > 1:
        for d_ in (0, 1, -1, 2, -2):
            if str(a + d_) in ov: fam = ov[str(a + d_)]; break
    rows.append(dict(plan=len(rows) + 1, image_debut=a, image_fin=b, debut_s=round(a / FPS, 2), fin_s=round(b / FPS, 2),
                     duree_s=round(dur, 2), famille=fam, luma=round(yy, 1), sat=round(ss, 1), rouge=round(rr, 3),
                     vert=round(vv, 3), beige=round(bb, 3), part_nb=round(nbfrac, 2), micro=int(dur < 0.3),
                     chroma=round(float(np.nanmedian(chroma[a:b])) if np.isfinite(chroma[a:b]).any() else -1, 2)))
# micro-plans (< 0,3 s, salves de montage) : heritent de l'ambiance du plan voisin (>= 0,3 s) le plus
# ressemblant (distance d'histogramme), sauf effets de montage / N&B / fondu.
full = [r for r in rows if not r['micro']]
for r in rows:
    if not r['micro'] or r['famille'] in ('X_effet_montage', 'NB', 'OUTRO_fondu') or any(str(r['image_debut'] + d_) in ov for d_ in (-2, -1, 0, 1, 2)):
        continue
    m = (r['image_debut'] + r['image_fin']) // 2
    prev = [q for q in full if q['image_fin'] <= r['image_debut']][-1:]
    nxt = [q for q in full if q['image_debut'] >= r['image_fin']][:1]
    best = None
    for q in prev + nxt:
        qm = (q['image_debut'] + q['image_fin']) // 2
        dd = cv2.compareHist(F[m]['hist'], F[qm]['hist'], cv2.HISTCMP_BHATTACHARYYA)
        if best is None or dd < best[0]: best = (dd, q['famille'])
    if best: r['famille'] = best[1]
# famille de LUT des segments sans effet (X, N&B) : plan reel voisin le plus RESSEMBLANT (histogramme)
reals = [q for q in rows if q['famille'] not in ('X_effet_montage', 'NB')]
for r in rows:
    r['famille_lut'] = r['famille']
    if r['famille'] in ('X_effet_montage', 'NB'):
        m = (r['image_debut'] + r['image_fin']) // 2
        prev = [q for q in reals if q['image_fin'] <= r['image_debut']][-1:]
        nxt = [q for q in reals if q['image_debut'] >= r['image_fin']][:1]
        best = None
        for q in prev + nxt:
            qm = (q['image_debut'] + q['image_fin']) // 2
            dd = cv2.compareHist(F[m]['hist'], F[qm]['hist'], cv2.HISTCMP_BHATTACHARYYA)
            if best is None or dd < best[0]: best = (dd, q['famille'])
        if best: r['famille_lut'] = best[1]
os.makedirs(out, exist_ok=True)
with open(f'{out}/plans.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
# passages N&B : intervalles d'images consecutives
runs = []; i = 0
while i < n:
    if nb[i]:
        j = i
        while j + 1 < n and nb[j + 1]: j += 1
        if j - i + 1 >= 3: runs.append([i, j, round(i / FPS, 2), round((j + 1) / FPS, 2)])
        i = j + 1
    else:
        i += 1
json.dump(dict(mesure='chrominance YUV moyenne des tons moyens', seuil=3.0, passages=runs), open(f'{out}/nb_images.json', 'w'), indent=1)
fams = {}
for r in rows: fams.setdefault(r['famille'], [0, 0.0]); fams[r['famille']][0] += 1; fams[r['famille']][1] += r['duree_s']
print(len(rows), 'segments ;', sum(r['micro'] for r in rows), 'micro (< 0,3 s) ; duree totale', round(sum(r['duree_s'] for r in rows), 2), 's')
for f, (c, d) in sorted(fams.items()): print(f'  {f:22} {c:4} segments {d:7.2f} s')
print('passages N&B (>= 3 images):', [(r[2], r[3]) for r in runs])
