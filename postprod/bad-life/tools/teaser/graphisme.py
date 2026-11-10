#!/usr/bin/env python3
"""BAD LIFE — habillage graphique premium du teaser (doc 12 §12.9).

Identite reprise du titre du clip (0-7,4 s) :
  - « BAD LIFE » : capitales a empattements triangulaires de type « inscription romaine », grasses, inclinees,
    matiere or en fusion (etincelles, reflets vifs, liseré sombre) -> Cinzel 900 inclinee de 12 deg (alternative
    proche : la police exacte du clip n'est pas identifiee) ;
  - « LYPHIK X JAHSIK » : capitales lineales condensees blanches -> Bebas Neue (correspondance visuelle).
Toutes les matieres sont procedurales (calculees, aucune image importee) et deterministes (graine fixe).
Aucune fonction de ce module ne touche aux pixels des artistes : il produit des calques (RGBA) poses DERRIERE
les artistes par teaser.py, et un fond (decor) genere.
"""
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

RNG = np.random.default_rng(20261110)


def bruit(h, w, echelles=(4, 8, 16, 32, 64), graine=0):
    """Bruit fractal lisse (valeurs 0-1), deterministe."""
    g = np.random.default_rng(graine)
    acc = np.zeros((h, w), np.float32); tot = 0
    for k, e in enumerate(echelles):
        n = g.random((max(2, h // e), max(2, w // e))).astype(np.float32)
        acc += cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC) / (k + 1); tot += 1 / (k + 1)
    acc /= tot
    return (acc - acc.min()) / (acc.max() - acc.min() + 1e-6)


def masque_texte(txt, police, taille, inclinaison=0.0, approche=0.0, sur=2):
    """Masque (0-1) du texte, sur-echantillonne x sur puis reduit (bords nets), incline (cisaillement) si demande."""
    f = ImageFont.truetype(police, int(taille * sur))
    adv = [f.getlength(c) for c in txt]
    tw = int(sum(adv) + approche * sur * (len(txt) - 1)) + 40 * sur
    bb = f.getbbox(txt); th = bb[3] - bb[1]
    pad = int(0.25 * th) + 20 * sur
    W = tw + int(abs(inclinaison) * (th + 2 * pad)) + 2 * pad; H = th + 2 * pad
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im); x = pad + int(abs(inclinaison) * H / 2)
    for c, a in zip(txt, adv):
        d.text((x, pad - bb[1]), c, font=f, fill=255); x += a + approche * sur
    m = np.asarray(im).astype(np.float32) / 255
    if inclinaison:
        M = np.float32([[1, -inclinaison, inclinaison * H / 2], [0, 1, 0]])
        m = cv2.warpAffine(m, M, (W, H), flags=cv2.INTER_CUBIC)
    m = cv2.resize(m, (W // sur, H // sur), interpolation=cv2.INTER_AREA)
    ys, xs = np.nonzero(m > 0.01)
    m = m[max(0, ys.min() - 30):ys.max() + 31, max(0, xs.min() - 30):xs.max() + 31]
    return np.clip(m, 0, 1)


def _relief(m, biseau):
    """Hauteur de biseau (0-1) et normale de surface d'apres la distance au bord."""
    d = cv2.distanceTransform((m > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    h = np.clip(d / biseau, 0, 1) ** 0.7
    h = cv2.GaussianBlur(h, (0, 0), 1.2)
    gx = cv2.Sobel(h, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(h, cv2.CV_32F, 0, 1, ksize=3)
    n = np.dstack([-gx * 3, -gy * 3, np.ones_like(h)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    return h, n


def matiere(m, style, graine=1):
    """Calque RGBA statique d'une matiere sur le masque m.
    style 'or'    : or en fusion (degrade orange -> or -> paille, veines lumineuses, grain metallique),
                    reflets rouges sur les faces tournees vers le bas (lumiere rouge du clip), liseré sombre ;
    style 'metal' : metal clair brosse, reflet rouge, liseré sombre ;
    style 'blanc' : blanc casse leger relief (textes secondaires)."""
    H, W = m.shape
    big = max(H, W)
    biseau = {'or': 0.055, 'metal': 0.05, 'blanc': 0.03}[style] * min(big, 700)
    h, n = _relief(m, max(biseau, 2.5))
    L = np.array([-0.45, -0.65, 0.62], np.float32); L /= np.linalg.norm(L)
    diff = np.clip((n * L).sum(axis=2), 0, 1)
    Hv = np.array([-0.2, -0.35, 0.92], np.float32); Hv /= np.linalg.norm(Hv)
    spec = np.clip((n * Hv).sum(axis=2), 0, 1) ** 28
    bas = np.clip(n[..., 1], 0, 1)                                         # faces tournees vers le bas
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    if style == 'or':
        nz = bruit(H, W, (8, 16, 32, 64), graine)
        veine = np.exp(-((nz - 0.5) / 0.025) ** 2) * 0.6                   # veines de metal en fusion (discretes)
        grain = bruit(H, W, (1, 2), graine + 7)
        xx_ = np.arange(W, dtype=np.float32)[None, :]
        stries = np.clip(np.sin((xx_ + yy * H * 0.9) / (0.075 * W) * 6.283) * 0.5 + 0.5, 0, 1) ** 6   # reflets diagonaux
        g2 = np.random.default_rng(graine + 11); pail = (g2.random((H, W)) > 0.9965).astype(np.float32)
        pail = cv2.GaussianBlur(pail, (0, 0), 0.8) * 6
        base = np.dstack([0.98 - 0.25 * yy, 0.62 - 0.32 * yy + 0.10 * (1 - yy), 0.14 - 0.10 * yy]).astype(np.float32)
        base = base * (0.70 + 0.45 * nz[..., None]) * (0.85 + 0.25 * grain[..., None])
        col = base * (0.35 + 0.85 * diff[..., None])
        fin = bruit(H, W, (2, 3, 5), graine + 5)                              # grain d'or fin et scintillant
        col *= (0.88 + 0.30 * fin[..., None])
        col += veine[..., None] * np.array([1.0, 0.78, 0.35], np.float32) * 0.0   # (veines retirees : effet « courbes de niveau »)
        col += (stries * (0.4 + 0.6 * diff))[..., None] * np.array([1.0, 0.85, 0.55], np.float32) * 0.35
        col += pail[..., None] * np.array([1.0, 0.95, 0.8], np.float32)
        col += spec[..., None] * np.array([1.0, 0.95, 0.80], np.float32) * 1.3
        col += bas[..., None] * np.array([0.95, 0.12, 0.06], np.float32) * 0.55   # reflet rouge
        bord = np.array([0.20, 0.06, 0.01], np.float32)
    elif style == 'metal':
        grain = bruit(H, W, (1, 2), graine + 3)
        brosse = cv2.blur(grain, (31, 1))
        base = np.dstack([0.88 + 0 * yy, 0.88 - 0.05 * yy, 0.90 - 0.08 * yy]).astype(np.float32) * (0.85 + 0.25 * brosse[..., None])
        bande = np.exp(-((yy - 0.62) / 0.10) ** 2)                          # bande de reflet rouge (environnement)
        col = base * (0.45 + 0.70 * diff[..., None])
        col = col * (1 - 0.55 * bande[..., None]) + bande[..., None] * np.array([0.92, 0.10, 0.08], np.float32) * 0.75
        col += spec[..., None] * 1.2 + bas[..., None] * np.array([0.9, 0.1, 0.05], np.float32) * 0.35
        bord = np.array([0.10, 0.02, 0.02], np.float32)
    else:
        col = np.ones((H, W, 3), np.float32) * np.array([0.96, 0.95, 0.93]) * (0.82 + 0.25 * diff[..., None]) + spec[..., None] * 0.4
        bord = np.array([0.05, 0.02, 0.02], np.float32)
    lis = np.clip(cv2.dilate(m, np.ones((5, 5), np.uint8)) - m, 0, 1) if style != 'blanc' else np.zeros_like(m)
    rgb = np.clip(col, 0, 1) * m[..., None] + bord * lis[..., None]
    a = np.clip(m + lis, 0, 1)
    return np.dstack([rgb, a]).astype(np.float32), h


def profondeur(m, couleur, n_pas, dx=0.55, dy=1.0):
    """Extrusion 3D : copies decalees vers le bas-droite, de plus en plus sombres (relief)."""
    H, W = m.shape
    acc = np.zeros((H + n_pas * 2, W + n_pas * 2, 4), np.float32)
    for k in range(n_pas, 0, -1):
        ox, oy = int(round(k * dx)), int(round(k * dy))
        sh = (0.35 + 0.65 * (1 - k / n_pas))
        c = np.array(couleur, np.float32) * sh
        sl = acc[oy:oy + H, ox:ox + W]
        sl[..., :3] = sl[..., :3] * (1 - m[..., None]) + c * m[..., None]; sl[..., 3] = np.maximum(sl[..., 3], m)
    return acc


def ombre(m, flou, opacite):
    a = cv2.GaussianBlur(m, (0, 0), flou) * opacite
    return np.dstack([np.zeros(m.shape + (3,), np.float32), a])


def lueur(m, couleur, flou, force):
    a = np.clip(cv2.GaussianBlur(m, (0, 0), flou) * force, 0, 1)
    return np.dstack([np.ones(m.shape + (3,), np.float32) * np.array(couleur, np.float32), a])


def poser(dst, src, x, y, opacite=1.0, additif=False):
    """Compose un calque RGBA src sur dst (RGBA float) en (x, y) coin haut-gauche, avec decoupe aux bords."""
    H, W = dst.shape[:2]; h, w = src.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]; a = s[..., 3:4] * opacite
    d = dst[y0:y1, x0:x1]
    if additif:
        d[..., :3] = np.clip(d[..., :3] + s[..., :3] * a, 0, 1); d[..., 3:4] = np.maximum(d[..., 3:4], a * 0)
    else:
        d[..., :3] = d[..., :3] * (1 - a) + s[..., :3] * a
        d[..., 3:4] = d[..., 3:4] * (1 - a) + a


class Titre:
    """Bloc titre pre-calcule (matiere + extrusion + ombre + lueur) ; seuls l'eclat et l'opacite varient."""

    def __init__(self, txt, police, taille, style, inclinaison=0.0, approche=0.0, extrusion=0, coul_ext=(0.35, 0.05, 0.02),
                 lueur_coul=(1.0, 0.35, 0.05), lueur_force=0.0, graine=1):
        self.m = masque_texte(txt, police, taille, inclinaison, approche)
        self.mat, self.h = matiere(self.m, style, graine)
        h, w = self.m.shape; e = extrusion; P = 40
        self.img = np.zeros((h + 2 * P + 2 * e, w + 2 * P + 2 * e, 4), np.float32)
        poser(self.img, ombre(self.m, 14, 0.85), P + e // 2 + 6, P + e + 12)
        if lueur_force: poser(self.img, lueur(self.m, lueur_coul, 22, lueur_force), P, P)
        if e: poser(self.img, profondeur(self.m, coul_ext, e), P, P)
        poser(self.img, self.mat, P, P)
        self.ox, self.oy = P, P
        ys, xs = np.nonzero(self.m > 0.05); self.encre = (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))
        self.w, self.h_ = self.img.shape[1], self.img.shape[0]

    def rendu(self, eclat=None, revele=1.0, chaleur=0.0):
        """eclat : position (0-1) d'une bande de lumiere diagonale qui traverse les lettres (None = aucune) ;
        revele : 0-1, devoilement gauche -> droite par un front incandescent ; chaleur : surbrillance globale."""
        out = self.img.copy()
        h, w = self.m.shape
        if eclat is not None:
            xx = np.arange(w, dtype=np.float32)[None, :]; yy = np.arange(h, dtype=np.float32)[:, None]
            pos = (eclat * 1.6 - 0.3) * (w + h)
            b = np.exp(-(((xx + yy * 0.6) - pos) / (0.05 * w)) ** 2) * self.m
            sl = out[self.oy:self.oy + h, self.ox:self.ox + w]
            sl[..., :3] = np.clip(sl[..., :3] + b[..., None] * np.array([1.0, 0.92, 0.75]) * 0.9, 0, 1)
        if chaleur > 0:
            sl = out[self.oy:self.oy + h, self.ox:self.ox + w]
            sl[..., :3] = np.clip(sl[..., :3] + chaleur * self.m[..., None] * np.array([1.0, 0.55, 0.15]), 0, 1)
        if revele < 1:
            W_ = out.shape[1]; front = revele * (W_ + 120) - 60
            xx = np.arange(W_, dtype=np.float32)[None, :]
            vis = np.clip((front - xx) / 40, 0, 1)
            hot = np.exp(-((xx - front) / 22) ** 2)
            out[..., :3] = np.clip(out[..., :3] + hot[..., None] * np.array([1.0, 0.75, 0.35]) * out[..., 3:4] * 1.2, 0, 1)
            out[..., 3] *= vis[0]
        return out


def etincelles(t, t0, n, cx, cy, etendue, graine):
    """Braises qui s'elevent depuis la zone du titre apres t0 (decor) : liste (x, y, rayon, intensite)."""
    if t < t0: return []
    g = np.random.default_rng(graine)
    pts = []
    for k in range(n):
        naissance = t0 + g.random() * 6.0
        vie = 1.4 + g.random() * 1.8
        u = (t - naissance) / vie
        if not (0 <= u <= 1): continue
        x = cx + (g.random() - 0.5) * etendue + 30 * np.sin(6.28 * (u * 0.8 + g.random()))
        y = cy + (g.random() - 0.3) * 120 - u * (180 + 220 * g.random())
        pts.append((x, y, 1.2 + 2.2 * g.random(), (1 - u) * (0.6 + 0.4 * g.random()) * min(1, u * 8)))
    return pts


def dessiner_etincelles(img, pts):
    H, W = img.shape[:2]
    for x, y, r, i in pts:
        xi, yi = int(x), int(y); R = int(r * 4) + 2
        if not (R <= xi < W - R and R <= yi < H - R): continue
        yy, xx = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float32)
        g = np.exp(-(xx ** 2 + yy ** 2) / (2 * r * r)) * i
        img[yi - R:yi + R + 1, xi - R:xi + R + 1] = np.clip(img[yi - R:yi + R + 1, xi - R:xi + R + 1] + g[..., None] * np.array([1.0, 0.62, 0.22]), 0, 1)


class Fond:
    """Atmosphere generee (decor) : noir profond, fumee rouge qui derive lentement, rayons de lumiere venus du
    haut, vignettage et grain fin fixe. Pre-calcule sur une texture plus grande, puis decale dans le temps."""

    def __init__(self, W, H):
        self.W, self.H = W, H
        self.fumee = cv2.GaussianBlur(bruit(H + 400, W + 400, (96, 192, 384), 11), (0, 0), 18)
        self.fumee2 = cv2.GaussianBlur(bruit(H + 400, W + 400, (64, 128, 256), 12), (0, 0), 12)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        ang = np.arctan2(xx - W / 2, yy + 300)
        self.rayons = (0.5 + 0.5 * np.cos(ang * 23)) * (0.5 + 0.5 * np.cos(ang * 9 + 1.3))
        self.rayons *= np.exp(-yy / (H * 0.55)) * np.exp(-((xx - W / 2) / (W * 0.6)) ** 2)
        self.vign = np.clip(1 - 0.55 * (((xx - W / 2) / (W / 2)) ** 2 * 0.7 + ((yy - H * 0.45) / (H / 2)) ** 2), 0.25, 1)
        self.grain = (bruit(H, W, (1, 2), 13) - 0.5) * 0.018

    def rendu(self, t):
        W, H = self.W, self.H
        o1 = int(200 + 60 * np.sin(t * 0.21)); o2 = int(200 - t * 9) % 400
        f1 = self.fumee[o2:o2 + H, o1:o1 + W]; f2 = self.fumee2[200 - int(t * 5) % 200:200 - int(t * 5) % 200 + H, 200:200 + W]
        fum = np.clip((f1 * 0.6 + f2 * 0.4 - 0.30) * 1.6, 0, 1) ** 1.5
        haut = np.linspace(0.55, 1.0, H, dtype=np.float32)[:, None]          # plus sombre en haut
        img = np.zeros((H, W, 3), np.float32) + 0.010
        img += (fum * haut)[..., None] * np.array([0.60, 0.05, 0.035], np.float32) * 0.50
        img += (self.rayons * (0.75 + 0.25 * np.sin(t * 0.7)))[..., None] * np.array([0.9, 0.25, 0.12], np.float32) * 0.16
        img = img * self.vign[..., None] + self.grain[..., None]
        return np.clip(img, 0, 1)
