#!/usr/bin/env python3
"""BAD LIFE — teaser de sortie vertical 9:16, 30 s (doc 12).

Principe (meme regle que le master) : out = alpha * ARTISTES + (1 - alpha) * (DECOR + effets + textes)
  - ARTISTES = pixels du master V5.1 recadres / redimensionnes (homothetie, jamais deformes) ;
  - effets (assombrissement, lueur rouge, vignettage, eclairs de coupe, pulsations) : decor uniquement ;
  - textes poses DERRIERE les artistes (jamais par-dessus) ou dans les bandes hors image ;
  - seule exception : l'ouverture au noir des 0,8 premieres secondes (transition), exclue du controle.
Entrees : master 4K, masques alpha (1080p, un par image source), table des plans, liste de montage (EDL).
Sortie  : images RGB 1080x1920 sur stdout (rawvideo) + qc_teaser.csv (ecart artistes par image).
Usage   : teaser.py MASTER.mp4 MATTE_DIR PLANS.csv EDL.json POLICE_TITRE POLICE_TEXTE POLICE_TEXTE_FINE QC.csv > video.rgb
"""
import csv, json, subprocess, sys, bisect
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

MST, MATTE, PLANS, EDLP, F_TITRE, F_TEXTE, F_FINE, QCP = sys.argv[1:9]
W, H = 1080, 1920
SW, SH = 3840, 2160                       # master
BAND_Y0, BAND_H = 560, 720                # bande cinema (duos)
ROUGE = (226, 27, 27); BLANC = (245, 245, 245)
E = json.load(open(EDLP)); FPS = E['fps']; NF = int(round(E['duree_s'] * FPS)); TX = E['textes']
plans = sorted((int(p['image_debut']), int(p['image_fin'])) for p in csv.DictReader(open(PLANS)))
p_starts = [a for a, _ in plans]
def plan_of(i): return plans[bisect.bisect(p_starts, i) - 1]


def alpha_src(i):
    return cv2.imread(f'{MATTE}/alpha_{i:05d}.png', cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0


def persons(i):
    """Composantes 'personne' du masque (coordonnees 1080p) : liste (x0, x1, surface)."""
    a = (alpha_src(i) > 0.5).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(a, 8)
    out = [(st[k, 0], st[k, 0] + st[k, 2], st[k, 4]) for k in range(1, n) if st[k, 4] > 4000]
    return sorted(out, key=lambda c: -c[2])


def centre_x(frames, largeur):
    """Centre horizontal (coordonnees 1080p) d'une fenetre de largeur donnee : tous les artistes s'ils tiennent
    dedans, sinon la plus grande personne. Mediane sur quelques images du plan (cadre fixe par plan)."""
    cs = []
    for i in frames[::max(1, len(frames) // 6)]:
        ps = persons(i)
        if not ps: continue
        x0, x1 = min(p[0] for p in ps), max(p[1] for p in ps)
        cs.append((x0 + x1) / 2 if x1 - x0 <= largeur * 0.92 else (ps[0][0] + ps[0][1]) / 2)
    return float(np.median(cs)) if cs else 960.0


# ---------- plan de rendu image par image ----------
segs = []
for s in E['segments']:
    n0, n1 = int(round(s['t0'] * FPS)), int(round(s['t1'] * FPS))
    a = int(round(s['src'] * FPS))
    src = [a] * (n1 - n0) if s.get('fige') else list(range(a, a + n1 - n0))
    segs.append(dict(s, n0=n0, n1=n1, srcs=src))
cuts = [s['t0'] for s in E['segments'][1:]]
# cadrage fixe par (segment, plan source)
for s in segs:
    s['cx'] = {}
    for p in sorted({plan_of(i) for i in s['srcs']}):
        fr = [i for i in s['srcs'] if plan_of(i) == p]
        larg = (SH * 9 / 16) / 2 if s['disposition'] == 'plein' else 1620.0
        s['cx'][p] = centre_x(fr, larg)

polices = {}
def police(path, size):
    k = (path, int(size))
    if k not in polices: polices[k] = ImageFont.truetype(path, int(size))
    return polices[k]


def texte(layer, txt, font, cx, cy, fill, alpha=1.0, tracking=0.0, ombre=True):
    """Texte centre en (cx, cy) sur un calque RGBA PIL, avec espacement des lettres et ombre portee douce."""
    if alpha <= 0: return
    ws = [font.getbbox(ch)[2] - font.getbbox(ch)[0] if ch != ' ' else font.getlength(' ') for ch in txt]
    adv = [font.getlength(ch) for ch in txt]
    tw = sum(adv) + tracking * (len(txt) - 1)
    bb = font.getbbox(txt); th = bb[3] - bb[1]
    x = cx - tw / 2; y = cy - th / 2 - bb[1]
    tmp = Image.new('RGBA', layer.size, (0, 0, 0, 0)); d = ImageDraw.Draw(tmp)
    if ombre:
        sh = Image.new('RGBA', layer.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sh); xx = x
        for ch, a_ in zip(txt, adv): ds.text((xx + 4, y + 6), ch, font=font, fill=(0, 0, 0, int(200 * alpha))); xx += a_ + tracking
        sh = Image.fromarray(cv2.GaussianBlur(np.asarray(sh), (0, 0), 7)); layer.alpha_composite(sh)
    xx = x
    for ch, a_ in zip(txt, adv): d.text((xx, y), ch, font=font, fill=fill + (int(255 * alpha),)); xx += a_ + tracking
    layer.alpha_composite(tmp)


def ease_out(u): u = min(max(u, 0.0), 1.0); return 1 - (1 - u) ** 3
def fen(t, a, d): return min(max((t - a) / d, 0.0), 1.0)


def slam(t, t0, e0=1.10):
    """Apparition 'frappee' : echelle e0 -> 1,0 en 0,18 s, opacite 0 -> 1 en 0,06 s. e0 = 1,10 : le texte agrandi
    reste dans les marges de 60 px (aucun texte coupe, meme pendant l'animation)."""
    return e0 - (e0 - 1) * ease_out((t - t0) / 0.18), fen(t, t0, 0.06)


def calque_textes(t, disp):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    p = TX['presente']
    if p['de'] <= t < p['a']:
        out = 1 - fen(t, p['a'] - 0.35, 0.35)
        a1 = fen(t, p['de'], 0.55) * out; trk = 60 - 42 * ease_out((t - p['de']) / 1.2)
        texte(L, p['ligne1'], police(F_TITRE, 200), W / 2, 330, BLANC, a1, trk)
        texte(L, p['ligne2'], police(F_FINE, 66), W / 2, 478, (225, 225, 225), fen(t, p['de'] + 0.45, 0.5) * out, 6)
    r = TX['titre_revelation']
    if r['de'] <= t < r['a']:
        sc, a = slam(t, r['de']); a *= 1 - fen(t, r['a'] - 0.25, 0.25)
        texte(L, 'BAD LIFE', police(F_TITRE, 250 * sc), W / 2, 380, ROUGE, a, 8)
    if t >= TX['annonce_titre']['de']:
        sc, a = slam(t, TX['annonce_titre']['de'])
        texte(L, 'BAD LIFE', police(F_TITRE, 262 * sc), W / 2, 392, ROUGE, a, 8)
    ta = TX['annonce_artistes']['de']
    if t >= ta:
        u = ease_out((t - ta) / 0.3)
        texte(L, 'LYPHIK feat. JAHSIK', police(F_TEXTE, 70), W / 2, 205 + 30 * (1 - u), BLANC, fen(t, ta, 0.25), 2)
    td = TX['disponible']['de']
    if t >= td:
        wv = ease_out((t - td) / 0.15)                                   # bandeau rouge qui s'ouvre depuis le centre
        fd = police(F_TITRE, 86); larg = fd.getlength(TX['disponible']['texte']) + 3 * (len(TX['disponible']['texte']) - 1)
        bw = int((larg + 80) * wv); d.rectangle([W / 2 - bw / 2, 1318, W / 2 + bw / 2, 1436], fill=ROUGE + (240,))   # bandeau = texte + 40 px de chaque cote
        sc = 1.10 - 0.10 * ease_out((t - td - 0.08) / 0.18)
        texte(L, TX['disponible']['texte'], police(F_TITRE, 86 * sc), W / 2, 1377, BLANC, fen(t, td + 0.06, 0.08), 3)
    tc = TX['appel']['de']
    if t >= tc:
        u = ease_out((t - tc) / 0.3); a = fen(t, tc, 0.3)
        texte(L, TX['appel']['ligne1'], police(F_TEXTE, 58), W / 2, 1510 + 24 * (1 - u), BLANC, a, 3)
        texte(L, TX['appel']['ligne2'], police(F_TEXTE, 58), W / 2, 1584 + 24 * (1 - u), BLANC, a, 3)
    return np.asarray(L).astype(np.float32) / 255.0


# ---------- fond genere des bandes (decor graphique, sans image d'artiste) ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def fond_bandes(t):
    g = np.zeros((H, W, 3), np.float32) + 0.018
    for cy in (BAND_Y0 * 0.55, BAND_Y0 + BAND_H + (H - BAND_Y0 - BAND_H) * 0.45):
        r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - cy) / 420) ** 2)
        glow = np.exp(-r ** 2 * 2.2) * (0.20 + 0.04 * np.sin(2 * np.pi * t / 4.0))
        g += glow[..., None] * np.array([0.85, 0.06, 0.05], np.float32)
    sweep = np.exp(-(((xx - (t * 140) % (W * 1.6) + W * 0.3) + (yy - H / 2) * 0.35) / 90) ** 2) * 0.035
    g += sweep[..., None] * np.array([1.0, 0.35, 0.3], np.float32)
    return np.clip(g, 0, 1)

vy = (yy - H / 2) / (H / 2); vx = (xx - W / 2) / (W / 2)
VIGN = np.clip(1 - 0.42 * (vx ** 2 * 0.8 + vy ** 2), 0.35, 1)[..., None]


def effets_decor(img, t, disp):
    """Effets sur le DECOR seulement : assombrissement + virage rouge des ombres + vignettage + lumiere de coupe."""
    k = 0.80 if t < 5.2 else (0.86 if t < 12 else (0.90 if t < 20 else 0.74))
    bg = img * k
    lum = bg.mean(axis=2, keepdims=True)
    bg = bg * 0.78 + 0.22 * lum * np.array([1.45, 0.55, 0.50], np.float32)          # ombres vers le rouge
    if disp == 'plein': bg = bg * VIGN
    fl = 0.0
    for c in cuts:
        if 5.2 - 1e-6 <= c <= 20.0 + 1e-6 and 0 <= t - c < 0.12: fl = max(fl, 0.30 * np.exp(-(t - c) / 0.04))
    if TX['disponible']['de'] <= t < TX['disponible']['de'] + 0.2: fl = max(fl, 0.35 * np.exp(-(t - TX['disponible']['de']) / 0.06))
    if fl > 0: bg = bg + fl * np.array([1.0, 0.45, 0.40], np.float32) * (0.35 + lum)
    return np.clip(bg, 0, 1)


def cadre(F, A1, cx, sc, ow, oh):
    """Homothetie de facteur sc (filtre moyenneur en reduction) puis recadrage entier ow x oh centre sur cx (4K).
    Meme transformation pour l'image et pour le masque : les artistes ne sont jamais deformes."""
    fw, fh = int(round(SW * sc)), int(round(SH * sc))
    Fs = cv2.resize(F, (fw, fh), interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_CUBIC)
    As = cv2.resize(A1, (fw, fh), interpolation=cv2.INTER_LINEAR)
    x0 = int(np.clip(round(cx * sc - ow / 2), 0, fw - ow)); y0 = int(round((fh - oh) / 2))
    return Fs[y0:y0 + oh, x0:x0 + ow].astype(np.float32) / 255, As[y0:y0 + oh, x0:x0 + ow]


# ---------- decodage ----------
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
qw.writerow(['image', 't_s', 'image_source', 'disposition', 'px_artistes', 'ecart_max_artistes_vs_master', 'controle', 'texte_x_min', 'texte_x_max', 'texte_y_min', 'texte_y_max'])
out = sys.stdout.buffer
for s in segs:
    n = s['n1'] - s['n0']
    frames = decode(s['srcs'][0], 1 if s.get('fige') else n)
    cache = None
    for j in range(n):
        ni = s['n0'] + j; t = ni / FPS; si = s['srcs'][j]
        if cache is None or not s.get('fige'): cache = next(frames)
        F = cache
        cx = s['cx'][plan_of(si)] * 2                           # 4K
        A1 = alpha_src(si)
        if s['disposition'] == 'plein':
            z = 1.0 + 0.03 * j / max(n - 1, 1)                  # lente avancee (homothetie, aucune deformation)
            SUB, AL = cadre(F, A1, cx, H * z / SH, W, H)
            BG = effets_decor(SUB, t, 'plein')
        else:
            z = 1.0 + (0.06 * j / max(n - 1, 1) if s.get('fige') else 0.02 * j / max(n - 1, 1))
            sb, ab = cadre(F, A1, cx, BAND_H * z / SH, W, BAND_H)
            SUB = np.zeros((H, W, 3), np.float32); SUB[BAND_Y0:BAND_Y0 + BAND_H] = sb
            AL = np.zeros((H, W), np.float32); AL[BAND_Y0:BAND_Y0 + BAND_H] = ab
            BG = fond_bandes(t)
            BG[BAND_Y0:BAND_Y0 + BAND_H] = effets_decor(sb, t, 'bande')
            BG[BAND_Y0 - 4:BAND_Y0] = np.array(ROUGE, np.float32) / 255; BG[BAND_Y0 + BAND_H:BAND_Y0 + BAND_H + 4] = np.array(ROUGE, np.float32) / 255
        AL = np.where(AL >= 0.97, 1.0, AL)[..., None]
        T = calque_textes(t, s['disposition'])
        COMP = BG * (1 - T[..., 3:]) + T[..., :3] * T[..., 3:]                # textes poses sur le decor ...
        O = AL * SUB + (1 - AL) * COMP                                        # ... puis les artistes par-dessus
        fade = min(1.0, t / 0.8)
        if fade < 1: O = O * fade
        O8 = np.clip(O * 255 + 0.5, 0, 255).astype(np.uint8)
        m = AL[..., 0] >= 1.0
        ref = np.clip(SUB * 255 + 0.5, 0, 255).astype(np.uint8)
        dev = int(np.abs(O8[m].astype(np.int16) - ref[m]).max()) if m.any() else 0
        ys_, xs_ = np.nonzero(T[..., 3] > 0.5)                                  # emprise des lettres (hors ombre douce)
        bb = [int(xs_.min()), int(xs_.max()), int(ys_.min()), int(ys_.max())] if len(xs_) else ['', '', '', '']
        qw.writerow([ni, f'{t:.3f}', si, s['disposition'], int(m.sum()), dev, 'transition (ouverture au noir)' if fade < 1 else 'strict'] + bb)
        out.write(O8.tobytes())
        if ni % 100 == 0: print(f'teaser {ni}/{NF}', file=sys.stderr, flush=True)
qc.close()
print('TERMINE', file=sys.stderr)
