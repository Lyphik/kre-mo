#!/usr/bin/env python3
"""BAD LIFE — teaser de sortie vertical 9:16, 30 s, version PREMIUM (doc 12).

Principe (meme regle que le master) : out = alpha * ARTISTES + (1 - alpha) * (DECOR + effets + graphisme)
  - ARTISTES = pixels du master V5.1, seulement recadres / redimensionnes (meme facteur sur les deux axes) ;
  - effets, fond genere, braises et typographie : DECOR uniquement, toujours DERRIERE les artistes ;
  - seule exception : l'ouverture au noir des 0,8 premieres secondes (transition), exclue du controle strict.
Dispositions (EDL) :
  plein      : recadrage 9:16 plein ecran ; fenetre fixe par plan source, qui contient la tete de chaque artiste
               et garde le plus de pixels d'artistes visibles ;
  bande      : image 16:9 ENTIERE dans une bande centrale de 1080 x 608 sur fond genere (introduction, duo de la revelation) ;
  couverture : composition de pochette (20-30 s) : image ancree en bas de l'ecran (aucune coupe visible du corps),
               a l'echelle qui garde les artistes entiers et leurs tetes sous le bloc typographique ; le decor se
               fond vers le haut dans l'atmosphere generee ; typographie fixe au-dessus.
Sortie : images RGB 1080x1920 sur stdout (rawvideo) + QC.csv (ecart artistes, emprise des textes, tetes coupees).
Usage  : teaser.py MASTER.mp4 MATTE_DIR PLANS.csv EDL.json CINZEL_900 CINZEL_700 BEBAS_NEUE QC.csv
"""
import csv, json, subprocess, sys, bisect, os
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graphisme as G

MST, MATTE, PLANS, EDLP, CZ9, CZ7, BB, QCP = sys.argv[1:9]
W, H = 1080, 1920
SW, SH = 3840, 2160
BAND_Y0, BAND_H = 656, 608                # bande : largeur entiere de l'image 16:9 (aucune tete coupee)
TETE_MIN_Y = 990                       # couverture : tetes des artistes sous le bloc typographique
E = json.load(open(EDLP)); FPS = E['fps']; NF = int(round(E['duree_s'] * FPS)); TX = E['textes']
plans = sorted((int(p['image_debut']), int(p['image_fin'])) for p in csv.DictReader(open(PLANS)))
p_starts = [a for a, _ in plans]
def plan_of(i): return plans[bisect.bisect(p_starts, i) - 1]


def alpha_src(i):
    return cv2.imread(f'{MATTE}/alpha_{i:05d}.png', cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0


def personnes(i, frac=0.30):
    """Personnes significatives du masque (coordonnees 1080p) : (x0, x1, y0, y1, tete_x0, tete_x1).
    Tete = partie haute (18 % de la hauteur) de la silhouette. Personnes >= frac x la plus grande."""
    a = (alpha_src(i) > 0.5).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(a, 8)
    comps = [k for k in range(1, n) if st[k, 4] > 4000]
    if not comps: return []
    amax = max(st[k, 4] for k in comps); out = []
    for k in comps:
        if st[k, 4] < frac * amax: continue
        x, y, w, h = st[k, 0], st[k, 1], st[k, 2], st[k, 3]
        band = lab[y:y + max(4, int(0.18 * h)), x:x + w] == k
        cols = np.nonzero(band.any(axis=0))[0]
        out.append((x, x + w, y, y + h, x + cols.min(), x + cols.max()))
    return out


def echantillon(frames): return frames[::max(1, len(frames) // 6)] + [frames[-1]]


def centre_x(frames, largeur):
    """Fenetre de largeur donnee (1080p) : doit contenir la tete de chaque artiste (si c'est possible, sinon celle de
    la plus grande personne) ; parmi les positions possibles, celle qui garde le plus de pixels d'artistes."""
    acc = np.zeros(1920, np.float64); hx0, hx1 = 1e9, -1e9; big = None
    for i in echantillon(frames):
        acc += alpha_src(i).sum(axis=0)
        for p in personnes(i):
            hx0, hx1 = min(hx0, p[4]), max(hx1, p[5])
        ps = personnes(i, 0.999)
        if ps: big = ps[0] if big is None else (min(big[0], ps[0][0]), max(big[1], ps[0][1]), 0, 0, min(big[4], ps[0][4]), max(big[5], ps[0][5]))
    L = int(round(largeur)); cs = np.concatenate([[0], np.cumsum(acc)])
    masse = cs[L:] - cs[:-L]; x0s = np.arange(len(masse))
    ok = np.ones(len(masse), bool)
    if hx1 > hx0 and hx1 - hx0 <= L - 20:
        ok = (x0s <= hx0 - 10) & (x0s + L >= hx1 + 10)
    elif big is not None and big[5] - big[4] <= L - 20:
        ok = (x0s <= big[4] - 10) & (x0s + L >= big[5] + 10)
    if not ok.any(): ok[:] = True
    pen = np.abs(x0s + L / 2 - 960) / 960 * 1e-3 * (masse.max() + 1)
    sc = np.where(ok, masse - pen, -1e18)
    return float(np.argmax(sc) + L / 2)


def params_couverture(frames):
    """Echelle (par rapport au 1080p) et centre. Contrainte verticale : tetes sous TETE_MIN_Y. Si les silhouettes
    entieres tiennent en largeur a une taille suffisante (>= 80 % de l'echelle maximale), elles sont gardees entieres ;
    sinon (bras tendus, groupe large), l'echelle suit les tetes avec 160 px de marge de chaque cote."""
    x0, x1, y0, hx0, hx1 = 1e9, -1e9, 1e9, 1e9, -1e9
    for i in echantillon(frames):
        for p in personnes(i, 0.25):
            x0, x1, y0 = min(x0, p[0]), max(x1, p[1]), min(y0, p[2]); hx0, hx1 = min(hx0, p[4]), max(hx1, p[5])
    if x1 < x0: return 0.75, 960.0
    s_vert = min((H - TETE_MIN_Y) / max(1080 - y0, 1), 1.2)
    s_full = (W - 80) / max(x1 - x0, 1)
    if s_full >= 0.8 * s_vert: return min(s_full, s_vert), (x0 + x1) / 2
    return min((W - 80) / max(hx1 - hx0 + 320, 1), s_vert), (hx0 + hx1) / 2


# ---------- plan de rendu ----------
segs = []
for s in E['segments']:
    n0, n1 = int(round(s['t0'] * FPS)), int(round(s['t1'] * FPS)); a = int(round(s['src'] * FPS))
    srcs = [a] * (n1 - n0) if s.get('fige') else list(range(a, a + n1 - n0))
    segs.append(dict(s, n0=n0, n1=n1, srcs=srcs))
cuts = [s['t0'] for s in E['segments'][1:]]
for s in segs:
    s['cx'] = {}
    if s['disposition'] == 'couverture':
        s['sc_c'], cxc = params_couverture(s['srcs'])
        for p in {plan_of(i) for i in s['srcs']}: s['cx'][p] = cxc
        continue
    for p in sorted({plan_of(i) for i in s['srcs']}):
        fr = [i for i in s['srcs'] if plan_of(i) == p]
        larg = (SH * 9 / 16) / 2 if s['disposition'] == 'plein' else 1620.0
        s['cx'][p] = float(s['cx_1080']) if 'cx_1080' in s else centre_x(fr, larg)
    print(f"segment {s['t0']:.2f} {s['disposition']} cadres {sorted(round(v) for v in s['cx'].values())}", file=sys.stderr)

# ---------- graphisme (pre-calcule) ----------
FOND = G.Fond(W, H)
g_ly = G.Titre('LYPHIK', BB, 190, 'blanc', 0, 22, graine=21)
g_pr = G.Titre('présente…', CZ7, 54, 'or', 0.21, 2, graine=22)
g_badr = G.Titre('BAD', CZ9, 178, 'or', 0.21, -3, extrusion=8, lueur_force=0.5, graine=23)
g_lifer = G.Titre('LIFE', CZ9, 178, 'or', 0.21, -3, extrusion=8, lueur_force=0.5, graine=24)
g_bad = G.Titre('BAD', CZ9, 300, 'or', 0.21, -4, extrusion=12, lueur_force=0.55, graine=3)
g_life = G.Titre('LIFE', CZ9, 300, 'or', 0.21, -4, extrusion=12, lueur_force=0.55, graine=4)
g_ly2 = G.Titre('LYPHIK', BB, 78, 'blanc', 0, 4, graine=7)
g_ja2 = G.Titre('JAHSIK', BB, 78, 'blanc', 0, 4, graine=8)
g_ft = G.Titre('feat.', CZ7, 46, 'or', 0.21, 0, graine=9)
g_md = G.Titre(TX['disponible']['texte'], BB, 108, 'metal', 0.0, 2, extrusion=12, coul_ext=(0.30, 0.02, 0.02),
               lueur_coul=(0.9, 0.08, 0.05), lueur_force=0.35, graine=5)
g_cta = G.Titre(TX['appel']['texte'], BB, 50, 'blanc', 0.0, 3, graine=6)
# lettres de l'annonce (colonnes d'encre separees par des colonnes vides) pour l'entree en cascade
_prof = (g_md.m > 0.05).any(axis=0); _x = np.nonzero(_prof)[0]; _bords = [_x[0]]
for k in range(1, len(_x)):
    if _x[k] - _x[k - 1] > 1: _bords.append((_x[k] + _x[k - 1]) // 2)
_bords.append(_x[-1] + 1); MD_LETTRES = [(a + g_md.ox, b + g_md.ox) for a, b in zip(_bords[:-1], _bords[1:])]


def ease(u): u = min(max(u, 0.0), 1.0); return 1 - (1 - u) ** 3
def fen(t, a, d): return min(max((t - a) / d, 0.0), 1.0)


def poser_encre(L, T, img, xg, cy, opac=1.0):
    G.poser(L, img, int(round(xg - T.ox - T.encre[0])), int(round(cy - T.oy - (T.encre[2] + T.encre[3]) / 2)), opac)


def poser_centre(L, T, img, cx, cy, opac=1.0):
    poser_encre(L, T, img, cx - (T.encre[1] - T.encre[0]) / 2, cy, opac)


def eclat(t, t0s, d=0.55):
    for t0 in t0s:
        if t0 <= t < t0 + d: return (t - t0) / d
    return None


BAR = 4 * 0.6037
def calque_graphisme(t, L):
    """Typographie et braises poses sur le decor (calque L, RGBA plein ecran)."""
    p = TX['presente']
    if p['de'] <= t < p['a']:
        out = 1 - fen(t, p['a'] - 0.30, 0.30)
        poser_centre(L, g_ly, g_ly.rendu(revele=ease((t - p['de']) / 0.7), eclat=eclat(t, [p['de'] + 1.4])), W / 2, 400, out)
        poser_centre(L, g_pr, g_pr.rendu(), W / 2, 545, fen(t, p['de'] + 0.5, 0.5) * out)
    r = TX['titre_revelation']
    if r['de'] <= t < r['a']:
        out = 1 - fen(t, r['a'] - 0.25, 0.25); t2 = r['de'] + 0.25
        G.dessiner_etincelles(L[..., :3], G.etincelles(t, r['de'], 26, W / 2, 380, 640, 31))
        poser_centre(L, g_badr, g_badr.rendu(revele=ease((t - r['de']) / 0.26), chaleur=0.6 * np.exp(-max(t - r['de'], 0) / 0.15),
                                             eclat=eclat(t, [r['de'] + 0.95])), W / 2, 330, out)
        if t >= t2:
            poser_centre(L, g_lifer, g_lifer.rendu(revele=ease((t - t2) / 0.26), chaleur=0.6 * np.exp(-(t - t2) / 0.15),
                                                   eclat=eclat(t, [r['de'] + 1.05])), W / 2, 480, out)
    ta = TX['annonce_titre']['de']
    if t >= ta:
        G.dessiner_etincelles(L[..., :3], G.etincelles(t, ta, 70, W / 2, 560, 820, 21))
        gl = [ta + 1.582 + k * BAR for k in range(5)]
        poser_centre(L, g_bad, g_bad.rendu(revele=ease((t - ta) / 0.30), chaleur=0.55 * np.exp(-(t - ta) / 0.18), eclat=eclat(t, gl, 0.6)), W / 2, 392)
        tl = TX['annonce_titre']['de2']
        if t >= tl:
            poser_centre(L, g_life, g_life.rendu(revele=ease((t - tl) / 0.30), chaleur=0.55 * np.exp(-(t - tl) / 0.18),
                                                 eclat=eclat(t, [g + 0.12 for g in gl], 0.6)), W / 2, 598)
    tn = TX['annonce_artistes']['de']
    if t >= tn:
        u = ease((t - tn) / 0.35); a = fen(t, tn, 0.3); dy = 18 * (1 - u)
        gap = 22; w1 = g_ly2.encre[1] - g_ly2.encre[0]; w2 = g_ft.encre[1] - g_ft.encre[0]; w3 = g_ja2.encre[1] - g_ja2.encre[0]
        x = W / 2 - (w1 + w2 + w3 + 2 * gap) / 2
        poser_encre(L, g_ly2, g_ly2.rendu(), x, 205 + dy, a)
        poser_encre(L, g_ft, g_ft.rendu(), x + w1 + gap, 209 + dy, a)
        poser_encre(L, g_ja2, g_ja2.rendu(), x + w1 + gap + w2 + gap, 205 + dy, a)
    td = TX['disponible']['de']
    if t >= td:
        img = g_md.rendu(eclat=eclat(t, [td + 0.604, td + 0.604 + 2 * BAR], 0.6))
        x0 = int(round(W / 2 - (g_md.encre[1] + g_md.encre[0]) / 2 - g_md.ox)) ; cy = 812
        y0 = int(round(cy - g_md.oy - (g_md.encre[2] + g_md.encre[3]) / 2))
        for k, (a_, b_) in enumerate(MD_LETTRES):                              # cascade lettre par lettre
            tk = td + 0.018 * k;
            if t < tk: continue
            u = ease((t - tk) / 0.22); al = fen(t, tk, 0.10)
            a2 = 0 if k == 0 else a_; b2 = img.shape[1] if k == len(MD_LETTRES) - 1 else b_   # bandes jointives, sans recouvrement
            G.poser(L, img[:, a2:b2], x0 + a2, y0 - int(round(55 * (1 - u))), al)
    tc = TX['appel']['de']
    if t >= tc:
        u = ease((t - tc) / 0.35)
        poser_centre(L, g_cta, g_cta.rendu(), W / 2, 918 + 16 * (1 - u), fen(t, tc, 0.3))


def effets_decor(img, t, disp):
    """DECOR seulement : assombrissement, virage rouge des ombres, vignettage (plein), lumiere de coupe."""
    k = 0.80 if t < 5.2 else (0.86 if t < 12 else (0.90 if t < 20 else 0.80))
    bg = img * k; lum = bg.mean(axis=2, keepdims=True)
    bg = bg * 0.78 + 0.22 * lum * np.array([1.45, 0.55, 0.50], np.float32)
    if disp == 'plein': bg = bg * VIGN[:bg.shape[0]]
    fl = 0.0
    for c in cuts:
        if 5.2 - 1e-6 <= c <= 20.0 + 1e-6 and 0 <= t - c < 0.12: fl = max(fl, 0.30 * np.exp(-(t - c) / 0.04))
    td = TX['disponible']['de']
    if td <= t < td + 0.25: fl = max(fl, 0.30 * np.exp(-(t - td) / 0.07))
    if fl > 0: bg = bg + fl * np.array([1.0, 0.45, 0.40], np.float32) * (0.35 + lum)
    return np.clip(bg, 0, 1)


yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIGN = np.clip(1 - 0.42 * (((xx - W / 2) / (W / 2)) ** 2 * 0.8 + ((yy - H / 2) / (H / 2)) ** 2), 0.35, 1)[..., None]
OR_FILET = np.array([0.85, 0.62, 0.25], np.float32)


def cadre(F, A1, cx, sc, ow, oh, ancre_bas=False):
    """Homothetie sc (par rapport au 4K) puis fenetre ow x oh centree sur cx (4K). Si l'image reduite est plus etroite
    ou plus basse que la fenetre, elle est centree (horizontalement) / ancree en bas, le reste est vide (masque 0)."""
    fw, fh = int(round(SW * sc)), int(round(SH * sc))
    Fs = cv2.resize(F, (fw, fh), interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_CUBIC)
    As = cv2.resize(A1, (fw, fh), interpolation=cv2.INTER_LINEAR)
    sub = np.zeros((oh, ow, 3), np.float32); al = np.zeros((oh, ow), np.float32); pres = np.zeros((oh, ow), np.float32)
    if fw >= ow: x0 = int(np.clip(round(cx * sc - ow / 2), 0, fw - ow)); dx = 0
    else: x0 = 0; dx = (ow - fw) // 2
    if fh >= oh: y0 = int(round((fh - oh) / 2)) if not ancre_bas else fh - oh; dy = 0
    else: y0 = 0; dy = oh - fh if ancre_bas else (oh - fh) // 2
    ww, hh = min(ow, fw), min(oh, fh)
    sub[dy:dy + hh, dx:dx + ww] = Fs[y0:y0 + hh, x0:x0 + ww].astype(np.float32) / 255
    al[dy:dy + hh, dx:dx + ww] = As[y0:y0 + hh, x0:x0 + ww]; pres[dy:dy + hh, dx:dx + ww] = 1
    vis = (x0 / sc / 2, (x0 + ww) / sc / 2)                                  # partie source visible (1080p)
    return sub, al, pres, (dx, dy, ww, hh), vis


def tetes_coupees(si, vis):
    n = 0
    for p in personnes(si):
        if p[4] < vis[0] - 1 or p[5] > vis[1] + 1: n += 1
    return n


def decode(src0, n):
    cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{src0 / FPS:.4f}', '-i', MST, '-frames:v', str(n),
           '-vf', 'scale=in_color_matrix=bt709:in_range=limited:flags=lanczos,format=rgb24', '-f', 'rawvideo', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    for _ in range(n):
        b = p.stdout.read(SW * SH * 3)
        if len(b) < SW * SH * 3: raise RuntimeError(f'decodage incomplet a {src0}')
        yield np.frombuffer(b, np.uint8).reshape(SH, SW, 3)
    p.stdout.close(); p.wait()


qc = open(QCP, 'w', newline=''); qw = csv.writer(qc)
qw.writerow(['image', 't_s', 'image_source', 'disposition', 'px_artistes', 'ecart_max_artistes_vs_master', 'controle',
             'texte_x_min', 'texte_x_max', 'texte_y_min', 'texte_y_max', 'tetes_coupees'])
out = sys.stdout.buffer
SEL = {int(x) for x in os.environ.get('TEASER_IMAGES', '').split(',') if x}   # apercu : images choisies -> PNG
for s in segs:
    n = s['n1'] - s['n0']
    if SEL and not any(s['n0'] <= k < s['n1'] for k in SEL): continue
    frames = decode(s['srcs'][0], 1 if s.get('fige') else n); cache = None
    for j in range(n):
        ni = s['n0'] + j; t = ni / FPS; si = s['srcs'][j]
        if cache is None or not s.get('fige'): cache = next(frames)
        if SEL and ni not in SEL: continue
        F = cache; cx = s['cx'][plan_of(si)] * 2; A1 = alpha_src(si); u = j / max(n - 1, 1)
        if s['disposition'] == 'plein':
            SUB, AL, _, _, vis = cadre(F, A1, cx, H * (1.0 + 0.03 * u) / SH, W, H)
            COMP = effets_decor(SUB, t, 'plein')
        elif s['disposition'] == 'bande':
            sb, ab, pres, _, vis = cadre(F, A1, 1920.0, W / SW, W, BAND_H)        # image entiere, sans avancee (rien ne sort du cadre)
            SUB = np.zeros((H, W, 3), np.float32); SUB[BAND_Y0:BAND_Y0 + BAND_H] = sb
            AL = np.zeros((H, W), np.float32); AL[BAND_Y0:BAND_Y0 + BAND_H] = ab
            COMP = FOND.rendu(t)
            yb = np.arange(BAND_H, dtype=np.float32)[:, None]
            wb = np.clip(np.minimum(yb, BAND_H - 1 - yb) / 50, 0, 1)                 # le decor se fond aux bords de la bande
            COMP[BAND_Y0:BAND_Y0 + BAND_H] = COMP[BAND_Y0:BAND_Y0 + BAND_H] * (1 - wb[..., None]) + effets_decor(sb, t, 'bande') * wb[..., None]
            for yl in (BAND_Y0 - 2, BAND_Y0 + BAND_H):                                # filets or de la bande
                prof = np.exp(-((np.arange(W) - W / 2) / (W * 0.42)) ** 2)[None, :, None]
                COMP[yl:yl + 2] = COMP[yl:yl + 2] * (1 - 0.8 * prof) + OR_FILET * 0.8 * prof
        else:  # couverture
            z = 1.0 + (0.02 * u if s.get('fige') else 0.012 * u)   # avancee lente ; marges laterales conservees
            sb, ab, pres, (dx, dy, ww, hh), vis = cadre(F, A1, cx, s['sc_c'] * z / 2, W, H, ancre_bas=True)
            SUB, AL = sb, ab
            ytop = dy; wdec = np.clip((yy[:, :1] - ytop) / 300, 0, 1); wdec = wdec * wdec * (3 - 2 * wdec)
            if ww < W:
                side = np.clip(np.minimum(xx[:1] - dx, dx + ww - 1 - xx[:1]) / 120, 0, 1); wdec = wdec * side
            COMP = FOND.rendu(t) * (1 - wdec[..., None] * pres[..., None]) + effets_decor(sb, t, 'couverture') * (wdec[..., None] * pres[..., None])
        AL = np.where(AL >= 0.97, 1.0, AL)[..., None]
        L = np.zeros((H, W, 4), np.float32); calque_graphisme(t, L)
        COMP = COMP * (1 - L[..., 3:]) + L[..., :3]
        O = AL * SUB + (1 - AL) * COMP
        fade = min(1.0, t / 0.8)
        if fade < 1: O = O * fade
        O8 = np.clip(O * 255 + 0.5, 0, 255).astype(np.uint8)
        m = AL[..., 0] >= 1.0; ref = np.clip(SUB * 255 + 0.5, 0, 255).astype(np.uint8)
        dev = int(np.abs(O8[m].astype(np.int16) - ref[m]).max()) if m.any() else 0
        ys_, xs_ = np.nonzero(L[..., 3] > 0.5)
        bb = [int(xs_.min()), int(xs_.max()), int(ys_.min()), int(ys_.max())] if len(xs_) else ['', '', '', '']
        qw.writerow([ni, f'{t:.3f}', si, s['disposition'], int(m.sum()), dev, 'transition (ouverture au noir)' if fade < 1 else 'strict']
                    + bb + [tetes_coupees(si, vis)])
        if SEL: cv2.imwrite(os.path.join(os.environ.get('TEASER_PNG_DIR', '.'), f'image_{ni:04d}.png'), cv2.cvtColor(O8, cv2.COLOR_RGB2BGR))
        else: out.write(O8.tobytes())
        if ni % 100 == 0: print(f'teaser {ni}/{NF}', file=sys.stderr, flush=True)
qc.close()
print('TERMINE', file=sys.stderr)
