#!/usr/bin/env python3
"""BAD LIFE V5 — detection robuste des coupes sur le clip entier (etape 2).

Pourquoi : le detecteur V1-V4 (score de scene ffmpeg > 0.25) manquait 5 coupes sur 9 dans
l'extrait de test. Ici :
  - h[i] : distance de Bhattacharyya entre histogrammes HSV (couleur) des images i-1 et i ;
  - g[i] : difference moyenne de luminance (image floutee) entre i-1 et i ;
  - normalisation LOCALE : rapport a la mediane des 16 voisins, ce qui evite de confondre un
    mouvement rapide en 25 i/s dans un fichier 50 i/s (une image sur deux change) avec une coupe ;
  - flash : image(s) tres lumineuse(s) entre deux images semblables -> 'flash', pas une coupe.
Sortie : JSON des candidats (temps, image, scores, type presume) a VALIDER VISUELLEMENT.
Usage : detect_cuts.py SOURCE OUT.json
"""
import json, subprocess, sys
import numpy as np, cv2

src, outp = sys.argv[1], sys.argv[2]
W, H = 320, 180
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-vf', f'scale={W}:{H}:flags=area,format=bgr24',
                      '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
hists, grays, lum = [], [], []
while True:
    b = p.stdout.read(W * H * 3)
    if len(b) < W * H * 3: break
    im = np.frombuffer(b, np.uint8).reshape(H, W, 3)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1, 2], None, [16, 8, 8], [0, 180, 0, 256, 0, 256])
    hists.append(cv2.normalize(h, None).flatten())
    g = cv2.GaussianBlur(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), (5, 5), 0).astype(np.float32)
    grays.append(g); lum.append(g.mean())
n = len(hists); fps = 50.0
hd = np.zeros(n, np.float32); gd = np.zeros(n, np.float32); rs = np.zeros(n, np.float32); ec = np.ones(n, np.float32)
win = cv2.createHanningWindow((W, H), cv2.CV_32F)
for i in range(1, n):
    hd[i] = cv2.compareHist(hists[i - 1], hists[i], cv2.HISTCMP_BHATTACHARYYA)
    gd[i] = np.abs(grays[i] - grays[i - 1]).mean() / 255
    # residu STRUCTUREL apres compensation du mouvement global (correlation de phase) et
    # normalisation de la luminance : faible pour un panoramique ou une rampe de saturation,
    # eleve pour une vraie coupe.
    a, b = grays[i - 1], grays[i]
    (dx, dy), _ = cv2.phaseCorrelate(a, b, win)
    M = np.float32([[1, 0, -dx], [0, 1, -dy]])
    b2 = cv2.warpAffine(b, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    za = (a - a.mean()) / (a.std() + 1); zb = (b2 - b2.mean()) / (b2.std() + 1)
    rs[i] = 1 - float((za * zb).mean())          # 1 - correlation (0 = identique, ~1 = sans rapport)
    # correlation des CONTOURS (structure de l'image, independante de la couleur) : une rampe
    # couleur -> N&B garde ses contours (> 0.85) ; une coupe les change (< 0.5 mesure sur l'extrait)
    e1 = cv2.GaussianBlur(cv2.Canny(a.astype(np.uint8), 40, 120).astype(np.float32), (9, 9), 0)
    e2 = cv2.GaussianBlur(cv2.Canny(b2.astype(np.uint8), 40, 120).astype(np.float32), (9, 9), 0)
    ec[i] = float((e1 * e2).sum() / np.sqrt((e1 ** 2).sum() * (e2 ** 2).sum() + 1e-6))
lum = np.array(lum)


def local_ratio(x, i, k=8):
    nb = np.concatenate([x[max(0, i - k):i], x[i + 1:i + 1 + k]])
    return x[i] / (np.median(nb) + 1e-3)


cands = []
for i in range(1, n):
    rh, rg = local_ratio(hd, i), local_ratio(gd, i)
    strong = hd[i] > 0.30
    rel = hd[i] > 0.12 and rh > 4.0 and rg > 2.0
    if not (strong or rel) or ec[i] > 0.6:       # contours conserves -> pas une coupe (rampe N&B, flash)
        continue
    # flash : image tres claire dont les voisins (avant/apres la salve) se ressemblent
    kind = 'coupe'
    if lum[i] > lum[i - 1] + 25:
        j = i
        while j + 1 < n and lum[j + 1] > lum[i - 1] + 25 and j - i < 6: j += 1
        if j + 1 < n and cv2.compareHist(hists[i - 1], hists[j + 1], cv2.HISTCMP_BHATTACHARYYA) < 0.12:
            kind = 'flash'
    cands.append(dict(image=i, t=round(i / fps, 2), hist=round(float(hd[i]), 3), lum_diff=round(float(gd[i]), 4),
                      ratio_hist=round(float(rh), 1), ratio_lum=round(float(rg), 1),
                      residu=round(float(rs[i]), 3), contours=round(float(ec[i]), 3), type=kind))
# PAS de fusion des candidats consecutifs : deux coupes a une image d'intervalle signalent un INSERT
# d'une image (ou une salve). ERRATUM V5 : une fusion initiale masquait ces inserts (84,50 s) et une
# coupe suivant immediatement une salve de flashs (93,30 s).
merged = cands
json.dump(dict(images=n, fps=fps, candidats=merged), open(outp, 'w'), indent=1)
print(n, 'images ;', len(merged), 'candidats ;', sum(c['type'] == 'coupe' for c in merged), 'coupes presumees ;',
      sum(c['type'] == 'flash' for c in merged), 'flashs presumes')
