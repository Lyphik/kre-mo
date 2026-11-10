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
    """Fenetre de largeur donnee (1080p), cadre fixe par plan, choisie par un score calcule image par image :
      score = 3 x (part des images ou la tete de l'artiste principal - la plus grande personne - est entiere)
            - 1,5 x (nombre moyen de visages tranches par un bord)
            + (pixels d'artistes visibles, normalises).
    L'artiste principal est donc toujours privilegie ; on evite ensuite de couper un visage au bord ; enfin on garde
    le plus d'artistes possible."""
    L = int(round(largeur)); acc = np.zeros(1920, np.float64)
    x0s = np.arange(1920 - L + 1); princ = np.zeros(len(x0s)); coupes = np.zeros(len(x0s)); n = 0
    for i in echantillon(frames):
        acc += alpha_src(i).sum(axis=0); ps = personnes(i); n += 1
        if not ps: continue
        g = max(ps, key=lambda p: (p[1] - p[0]) * (p[3] - p[2]))
        princ += (x0s <= g[4] - 6) & (x0s + L >= g[5] + 6)
        for p in ps:
            a, b = p[4], p[5]
            coupes += ((x0s > a - 6) & (x0s < b + 6)) | ((x0s + L > a - 6) & (x0s + L < b + 6))
    cs = np.concatenate([[0], np.cumsum(acc)]); masse = cs[L:] - cs[:-L]
    score = 3 * princ / max(n, 1) - 1.5 * coupes / max(n, 1) + masse / (masse.max() + 1e-9)
    score -= np.abs(x0s + L / 2 - 960) / 960 * 1e-3
    return float(np.argmax(score) + L / 2)


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
_ep = TX.get('presente', {}).get('echelle', 1.0)
g_ly = G.Titre('LYPHIK', BB, int(190 * _ep), 'blanc', 0, int(22 * _ep), graine=21)
g_pr = G.Titre('présente…', CZ7, int(54 * _ep), 'or', 0.21, 2, graine=22)
g_badr = G.Titre('BAD', CZ9, 178, 'or', 0.21, -3, extrusion=8, lueur_force=0.5, graine=23)
g_lifer = G.Titre('LIFE', CZ9, 178, 'or', 0.21, -3, extrusion=8, lueur_force=0.5, graine=24)
K = 0.75                                                         # fin : proportions validees a 75 % (zone libre au-dessus des tetes)
g_bad = G.Titre('BAD', CZ9, int(300 * K), 'or', 0.21, -4, extrusion=10, lueur_force=0.55, graine=3)
g_life = G.Titre('LIFE', CZ9, int(300 * K), 'or', 0.21, -4, extrusion=10, lueur_force=0.55, graine=4)
g_ly2 = G.Titre('LYPHIK', BB, int(78 * K), 'blanc', 0, 4, graine=7)
g_ja2 = G.Titre('JAHSIK', BB, int(78 * K), 'blanc', 0, 4, graine=8)
g_ft = G.Titre('feat.', CZ7, int(46 * K), 'or', 0.21, 0, graine=9)
g_md1 = G.Titre(TX['disponible']['ligne1'], BB, 150, 'metal', 0.0, 3, extrusion=12, coul_ext=(0.30, 0.02, 0.02),
                lueur_coul=(0.9, 0.08, 0.05), lueur_force=0.35, graine=5)
g_md2 = G.Titre(TX['disponible']['ligne2'], BB, 150, 'metal', 0.0, 3, extrusion=12, coul_ext=(0.30, 0.02, 0.02),
                lueur_coul=(0.9, 0.08, 0.05), lueur_force=0.35, graine=15)
def lettres(T):
    """Bandes de colonnes (une par lettre) pour l'entree en cascade : colonnes d'encre separees par des colonnes vides."""
    prof = (T.m > 0.05).any(axis=0); x = np.nonzero(prof)[0]; b = [x[0]]
    for k in range(1, len(x)):
        if x[k] - x[k - 1] > 1: b.append((x[k] + x[k - 1]) // 2)
    b.append(x[-1] + 1); return [(a + T.ox, c + T.ox) for a, c in zip(b[:-1], b[1:])]
L_MD1, L_MD2 = lettres(g_md1), lettres(g_md2)


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
    p = TX.get('presente')                                                 # carton supprime dans la version definitive
    if p and p['de'] <= t < p['a']:
        out = 1 - fen(t, p['a'] - 0.30, 0.30)
        poser_centre(L, g_ly, g_ly.rendu(revele=ease((t - p['de']) / 0.7), eclat=eclat(t, [p['de'] + 1.4])), W / 2, p.get('y1', 400), out)
        poser_centre(L, g_pr, g_pr.rendu(), W / 2, p.get('y2', 545), fen(t, p['de'] + 0.5, 0.5) * out)
    r = TX.get('titre_revelation')                                         # retire dans la version definitive (passage en plein ecran)
    if r and r['de'] <= t < r['a']:
        out = 1 - fen(t, r['a'] - 0.25, 0.25); t2 = r['de'] + 0.25
        G.dessiner_etincelles(L[..., :3], G.etincelles(t, r['de'], 26, W / 2, 380, 640, 31))
        poser_centre(L, g_badr, g_badr.rendu(revele=ease((t - r['de']) / 0.26), chaleur=0.6 * np.exp(-max(t - r['de'], 0) / 0.15),
                                             eclat=eclat(t, [r['de'] + 0.95])), W / 2, 330, out)
        if t >= t2:
            poser_centre(L, g_lifer, g_lifer.rendu(revele=ease((t - t2) / 0.26), chaleur=0.6 * np.exp(-(t - t2) / 0.15),
                                                   eclat=eclat(t, [r['de'] + 1.05])), W / 2, 480, out)
    ta, tl, tf = TX['annonce_titre']['de'], TX['annonce_titre']['de2'], TX['annonce_titre']['a']
    if ta <= t < tf:
        sortie = 1 - fen(t, tf - 0.18, 0.18)                                 # le titre se dissipe juste avant l'annonce
        chal = 0.5 * fen(t, tf - 0.18, 0.18)
        G.dessiner_etincelles(L[..., :3], G.etincelles(t, ta, 40, W / 2, 330, 760, 21))
        poser_centre(L, g_bad, g_bad.rendu(revele=ease((t - ta) / 0.30), chaleur=0.55 * np.exp(-(t - ta) / 0.18) + chal,
                                           eclat=eclat(t, [ta + 1.582], 0.6)), W / 2, 280, sortie)
        if t >= tl:
            poser_centre(L, g_life, g_life.rendu(revele=ease((t - tl) / 0.30), chaleur=0.55 * np.exp(-(t - tl) / 0.18) + chal,
                                                 eclat=eclat(t, [ta + 1.70], 0.6)), W / 2, 435, sortie)
        tn = TX['annonce_artistes']['de']
        if t >= tn:
            u = ease((t - tn) / 0.35); a = fen(t, tn, 0.3) * sortie; dy = 14 * (1 - u)
            gap = 16; w1 = g_ly2.encre[1] - g_ly2.encre[0]; w2 = g_ft.encre[1] - g_ft.encre[0]; w3 = g_ja2.encre[1] - g_ja2.encre[0]
            x = W / 2 - (w1 + w2 + w3 + 2 * gap) / 2
            poser_encre(L, g_ly2, g_ly2.rendu(), x, 140 + dy, a)
            poser_encre(L, g_ft, g_ft.rendu(), x + w1 + gap, 143 + dy, a)
            poser_encre(L, g_ja2, g_ja2.rendu(), x + w1 + gap + w2 + gap, 140 + dy, a)
    td, tq = TX['disponible']['de'], TX['disponible']['a']
    if td <= t < tq:
        sortie = 1 - fen(t, tq - 0.35, 0.35); mont = -12 * fen(t, tq - 0.35, 0.35)
        for T, LL, cy, dt in ((g_md1, L_MD1, 255, 0.0), (g_md2, L_MD2, 415, 0.12)):
            img = T.rendu(eclat=eclat(t, [td + 0.882 + dt, td + 1.486 + dt], 0.55))
            x0 = int(round(W / 2 - (T.encre[1] + T.encre[0]) / 2 - T.ox)); y0 = int(round(cy + mont - T.oy - (T.encre[2] + T.encre[3]) / 2))
            for k, (a_, b_) in enumerate(LL):                                     # cascade lettre par lettre
                tk = td + dt + 0.022 * k
                if t < tk: continue
                u = ease((t - tk) / 0.22); al = fen(t, tk, 0.10) * sortie
                a2 = 0 if k == 0 else a_; b2 = img.shape[1] if k == len(LL) - 1 else b_
                G.poser(L, img[:, a2:b2], x0 + a2, y0 - int(round(55 * (1 - u))), al)


def effets_decor(img, t, disp):
    """DECOR seulement : assombrissement, virage rouge des ombres, vignettage (plein), lumiere de coupe."""
    k = 0.80 if t < 5.2 else (0.86 if t < 12 else (0.90 if t < 20 else 0.90))   # fin : decor lisible
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


BORDS_DECONTAMINES = E.get('bords_decontamines', True)


def champ_fond(SUB, a, sigma=10.0):
    """Champ de fond pour les effets de decor (correction du liseré clair, doc 12.13). Dans la bande de transition du
    masque (0 < alpha < 0,97), le pixel observe melange l'artiste et le fond d'origine ; appliquer l'effet de decor a ce
    melange n'assombrit que partiellement la part de fond et laisse un liseré plus clair que le decor voisin. On estime
    donc la couleur du fond derriere l'artiste a partir du decor voisin (moyenne ponderee gaussienne des pixels de decor
    pur) ; l'effet est calcule sur ce fond et applique a la seule part (1 - alpha) : sortie = pixel + (1 - alpha) x
    (fond modifie - fond). Les pixels opaques de l'artiste (alpha = 1) restent strictement identiques ; le decor pur
    (alpha ~ 0) est traite comme avant."""
    w = (a < 0.03).astype(np.float32)
    num = cv2.GaussianBlur(SUB * w[..., None], (0, 0), sigma); den = cv2.GaussianBlur(w, (0, 0), sigma)[..., None]
    bh = np.where(den > 1e-3, num / np.maximum(den, 1e-3), SUB)
    return np.where(w[..., None] > 0, SUB, bh).astype(np.float32)


DN = E.get('debruitage_decor')


def debruitage_decor(O, AL, Lalpha, prev):
    """Debruitage local du DECOR (doc 12.13) : seulement ou le pixel est du decor (1 - alpha), sombre (luma < seuil) et
    uni (faible detail local), hors textes. (1) lissage bilateral leger (preserve les contours, ecart de couleur < 3 codes) ;
    (2) filtre temporel recursif, applique seulement la ou l'image n'a pas bouge depuis l'image precedente (ecart < 3 codes) :
    aucun trainage sur les mouvements. Les pixels opaques des artistes (alpha = 1) ne sont jamais modifies."""
    O = O.astype(np.float32); lum = O.mean(axis=2)
    wd = np.clip((DN['seuil_luma'] / 255 - lum) / (24 / 255), 0, 1)
    det = cv2.GaussianBlur(np.abs(cv2.Laplacian(lum, cv2.CV_32F)), (0, 0), 2)
    wf = np.clip((0.020 - det) / 0.012, 0, 1)
    m = (1 - AL[..., 0]) * (1 - Lalpha) * wd * wf * DN.get('force', 1.0)
    if m.max() <= 0: return O
    Ob = cv2.bilateralFilter(O.astype(np.float32), 7, 3 / 255, 5)
    if prev is not None:
        immobile = np.clip(1 - cv2.GaussianBlur(np.abs(Ob - prev).mean(axis=2), (0, 0), 2) / (3 / 255), 0, 1)
        Ob = Ob + 0.5 * immobile[..., None] * (prev - Ob)
    return O + m[..., None] * (Ob - O)


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
    """Tetes tranchees par un bord du cadre (a cheval : ni entierement dedans, ni entierement dehors)."""
    n = 0
    for p in personnes(si):
        dedans = p[4] >= vis[0] - 1 and p[5] <= vis[1] + 1; dehors = p[5] <= vis[0] + 1 or p[4] >= vis[1] - 1
        if not dedans and not dehors: n += 1
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
SEL = {int(x) for x in os.environ.get('TEASER_IMAGES', '').split(',') if x}
PREV = {}                                                                      # image precedente du meme plan (filtre temporel)   # apercu : images choisies -> PNG
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
            av = 0.03 * u if t < 20.0 else 0.0                                 # fin : mouvements reels uniquement
            SUB, AL, _, _, vis = cadre(F, A1, cx, H * (1.0 + av) / SH, W, H)
            CHAMP = champ_fond(SUB, np.where(AL >= 0.97, 1.0, AL)) if BORDS_DECONTAMINES else SUB
            COMP = effets_decor(CHAMP, t, 'plein')
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
        if s['disposition'] == 'plein' and BORDS_DECONTAMINES:
            O = np.clip(SUB + (1 - AL) * (COMP - CHAMP), 0, 1)                 # seule la part de fond des pixels de bord change
        else:
            O = AL * SUB + (1 - AL) * COMP
        if DN and s['disposition'] == 'plein':
            cle = (s['t0'], plan_of(si))
            O = debruitage_decor(O, AL, L[..., 3], PREV.get(cle)); PREV.clear(); PREV[cle] = O
        fe = E.get('fondu_entree_video', 0.8)
        fade = min(1.0, t / fe) if fe > 0 else 1.0                              # ouverture au noir (supprimee dans la version definitive)
        fs = E.get('fondu_sortie_video')
        if fs and t > fs['de']: fade = min(fade, max(0.0, (E['duree_s'] - t) / fs['duree']))   # fondu de sortie discret
        if fade < 1: O = O * fade
        O8 = np.clip(O * 255 + 0.5, 0, 255).astype(np.uint8)
        m = AL[..., 0] >= 1.0; ref = np.clip(SUB * 255 + 0.5, 0, 255).astype(np.uint8)
        dev = int(np.abs(O8[m].astype(np.int16) - ref[m]).max()) if m.any() else 0
        ys_, xs_ = np.nonzero(L[..., 3] > 0.5)
        bb = [int(xs_.min()), int(xs_.max()), int(ys_.min()), int(ys_.max())] if len(xs_) else ['', '', '', '']
        qw.writerow([ni, f'{t:.3f}', si, s['disposition'], int(m.sum()), dev, ('transition (ouverture au noir)' if t < 1 else 'transition (fondu de sortie)') if fade < 1 else 'strict']
                    + bb + [tetes_coupees(si, vis)])
        if SEL: cv2.imwrite(os.path.join(os.environ.get('TEASER_PNG_DIR', '.'), f'image_{ni:04d}.png'), cv2.cvtColor(O8, cv2.COLOR_RGB2BGR))
        else: out.write(O8.tobytes())
        if ni % 100 == 0: print(f'teaser {ni}/{NF}', file=sys.stderr, flush=True)
qc.close()
print('TERMINE', file=sys.stderr)
