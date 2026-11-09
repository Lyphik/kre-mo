#!/usr/bin/env python3
"""BAD LIFE — generateur des LUT 3D "look" (intensite BALANCED).

Espace d'entree/sortie : Rec.709 / gamma BT.1886, RGB pleine echelle [0,1]
(ffmpeg convertit la plage TV 16-235 en RGB plein avant lut3d).

Le traitement est fait en Y'CbCr (Rec.709) pour separer luminance et chrominance :
  1. Restauration du point noir/blanc (source : noirs releves ~ code 23-27).
  2. Courbe de contraste "filmique" (pied doux, epaule douce) sur la luma seule.
  3. Saturation adaptative (vibrance) - forte sur les tons ternes, limitee sur la peau.
  4. Rouges : saturation renforcee (rouge profond et lumineux).
  5. Verts jaunatres de la cite -> legerement vers le sarcelle (palette cyan/petrole).
  6. Split-toning : ombres petrole/cyan, hautes lumieres ambre ; attenue sur la peau.
  7. Retour RGB avec compression de gamut (pas d'ecretage qui deforme la teinte).

Protection peau : ponderation par la "skin line" du vectorscope (~123 deg) et par la
chroma ; la peau ne subit ni rotation de teinte ni split-toning complet.
"""
import argparse
import numpy as np

KR, KB = 0.2126, 0.0722
KG = 1.0 - KR - KB


def rgb_to_ycc(r, g, b):
    y = KR * r + KG * g + KB * b
    return y, (b - y) / (2 * (1 - KB)), (r - y) / (2 * (1 - KR))


def ycc_to_rgb(y, cb, cr):
    r = y + 2 * (1 - KR) * cr
    b = y + 2 * (1 - KB) * cb
    g = (y - KR * r - KB * b) / KG
    return r, g, b


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def hue_weight(h, center_deg, width_deg):
    d = np.angle(np.exp(1j * (h - np.radians(center_deg))))
    return np.exp(-0.5 * (d / np.radians(width_deg)) ** 2)


def pchip(xp, yp):
    """Interpolation monotone (Fritsch-Carlson) : aucune inversion de tonalite."""
    xp, yp = np.asarray(xp, float), np.asarray(yp, float)
    h = np.diff(xp); d = np.diff(yp) / h
    m = np.zeros_like(yp)
    m[0], m[-1] = d[0], d[-1]
    for k in range(1, len(xp) - 1):
        if d[k - 1] * d[k] > 0:
            w1, w2 = 2 * h[k] + h[k - 1], h[k] + 2 * h[k - 1]
            m[k] = (w1 + w2) / (w1 / d[k - 1] + w2 / d[k])

    def f(x):
        x = np.clip(x, xp[0], xp[-1])
        i = np.clip(np.searchsorted(xp, x) - 1, 0, len(h) - 1)
        t = (x - xp[i]) / h[i]
        h00 = (1 + 2 * t) * (1 - t) ** 2; h10 = t * (1 - t) ** 2
        h01 = t * t * (3 - 2 * t); h11 = t * t * (t - 1)
        return h00 * yp[i] + h10 * h[i] * m[i] + h01 * yp[i + 1] + h11 * h[i] * m[i + 1]
    return f


# Presets du look. Toute modification = nouvelle version (ne jamais modifier une version publiee).
PRESETS = {
    # v1 : premier jet. Rejete en interne : bas-mediums trop ecrases, peaux foncees bleuies.
    'v1': dict(
        black_in=0.035, white_in=0.975, black_out=0.004,
        curve_x=[0.0, 0.10, 0.25, 0.45, 0.70, 0.90, 1.0],
        curve_y=[0.0, 0.075, 0.215, 0.445, 0.725, 0.915, 0.985],
        sat_global=1.30, vibrance=0.55, sat_skin_max=1.12,
        red_center=103, red_width=14, red_gain=0.45,
        green_center=212, green_width=32, green_rot=16,
        shadow_hue=300, shadow_amt=0.030,
        high_hue=148, high_amt=0.018,
        skin_center=123, skin_width=20, skin_luma_gate=(0.03, 0.12),
    ),
}
# v2 : bas-mediums releves (detail dans les peaux foncees), split-toning des ombres reduit,
# protection peau etendue aux basses lumieres.
PRESETS['v2'] = dict(PRESETS['v1'],
    black_in=0.030,
    curve_y=[0.0, 0.092, 0.240, 0.462, 0.735, 0.918, 0.985],
    shadow_amt=0.022, skin_width=24, skin_luma_gate=(0.004, 0.035),
    sat_skin_max=1.10,
)
# v3 : contraste par le pied de courbe (noirs profonds, luma des visages conservee a +/-5 %),
# plus d'etirement global du noir ; teinte petrole des ombres reservee aux pixels deja froids
# (jamais sur neutres/chauds => jamais sur la peau, meme desaturee) ; ambre reduit.
PRESETS['v3'] = dict(PRESETS['v2'],
    black_in=0.0, white_in=1.0, black_out=0.0,
    curve_x=[0.0, 0.035, 0.06, 0.10, 0.20, 0.45, 0.70, 0.90, 1.0],
    curve_y=[0.0, 0.006, 0.030, 0.095, 0.200, 0.455, 0.725, 0.915, 0.985],
    skin_center=132, skin_width=24,
    shadow_cool_only=True, shadow_amt=0.026,
    high_amt=0.014, high_start=0.55,
)
# --- V4 : deux LUT melangees par le matte des artistes (tools/v4/composite.py) ---
# v4_decor : appliquee hors personnes. Contraste plus marque, noirs plus profonds (sans boucher :
#            0.10 -> 0.090), rouges plus riches, cyan/petrole renforce dans les ombres froides.
PRESETS['v4_decor'] = dict(PRESETS['v3'],
    curve_x=[0.0, 0.035, 0.06, 0.10, 0.20, 0.45, 0.70, 0.90, 1.0],
    curve_y=[0.0, 0.003, 0.022, 0.090, 0.190, 0.455, 0.745, 0.925, 0.985],
    sat_global=1.34, red_gain=0.70, red_width=16,
    shadow_amt=0.036, high_amt=0.016,
)
# v4_sujets : appliquee sur les personnes. Carnations et vetements proteges : pas de cyan, pas de
#             rotation des verts (un maillot vert reste vert), saturation moderee, ambre tres leger.
#             Noirs approfondis comme le decor, visages (0.10-0.25) conserves.
PRESETS['v4_sujets'] = dict(PRESETS['v3'],
    curve_x=[0.0, 0.035, 0.06, 0.10, 0.20, 0.45, 0.70, 0.90, 1.0],
    curve_y=[0.0, 0.004, 0.026, 0.095, 0.200, 0.455, 0.725, 0.915, 0.985],
    sat_global=1.22, vibrance=0.40, red_gain=0.50, red_width=16,
    green_rot=0, shadow_amt=0.0, high_amt=0.008,
)
P = PRESETS['v3']


def look(r, g, b, p=P):
    y, cb, cr = rgb_to_ycc(r, g, b)
    # 1. points noir / blanc
    y = (y - p['black_in']) / (p['white_in'] - p['black_in'])
    cb = cb / (p['white_in'] - p['black_in']); cr = cr / (p['white_in'] - p['black_in'])
    y = np.clip(y, 0, 1)
    # 2. contraste sur la luma
    y2 = pchip(p['curve_x'], p['curve_y'])(y)
    y2 = p['black_out'] + y2 * (1 - p['black_out'])
    # la chroma suit le rapport de luma dans les basses lumieres (pas de couleur dans le noir pur)
    ratio = np.where(y > 1e-4, np.clip(y2 / np.maximum(y, 1e-4), 0.6, 1.4), 1.0)
    c = np.hypot(cb, cr) * ratio
    h = np.arctan2(cr, cb)
    # ponderations
    skin = hue_weight(h, p['skin_center'], p['skin_width']) * (1 - smoothstep(0.10, 0.20, c)) \
        * smoothstep(p['skin_luma_gate'][0], p['skin_luma_gate'][1], y2)
    red = hue_weight(h, p['red_center'], p['red_width']) * smoothstep(0.06, 0.14, c)
    green = hue_weight(h, p['green_center'], p['green_width']) * smoothstep(0.01, 0.04, c)
    # 3-4. saturation
    gain = p['sat_global'] + p['vibrance'] * (1 - smoothstep(0.0, 0.18, c))
    gain = gain * (1 - skin) + np.minimum(gain, p['sat_skin_max']) * skin
    gain = gain + p['red_gain'] * red * (1 - skin)
    c = c * gain
    # 5. rotation des verts vers le sarcelle (jamais sur la peau)
    h = h + np.radians(p['green_rot']) * green * (1 - skin)
    cb, cr = c * np.cos(h), c * np.sin(h)
    # 6. split-toning
    protect = 1 - 0.85 * skin
    sh = p['shadow_amt'] * (1 - smoothstep(0.0, 0.55, y2)) * smoothstep(0.0, 0.08, y2) * protect
    if p.get('shadow_cool_only'):
        # uniquement les pixels deja froids et suffisamment chromatiques (teinte fiable)
        cool = smoothstep(0.0, 0.6, np.cos(h - np.radians(p['shadow_hue'])))
        sh = sh * cool * smoothstep(0.006, 0.025, c)
    hi = p['high_amt'] * smoothstep(p.get('high_start', 0.45), 1.0, y2) \
        * (1 - smoothstep(0.92, 1.0, y2)) * protect
    cb = cb + sh * np.cos(np.radians(p['shadow_hue'])) + hi * np.cos(np.radians(p['high_hue']))
    cr = cr + sh * np.sin(np.radians(p['shadow_hue'])) + hi * np.sin(np.radians(p['high_hue']))
    # 7. compression de gamut : on reduit la chroma (teinte conservee) au lieu d'ecreter
    r2, g2, b2 = ycc_to_rgb(y2, cb, cr)
    k = np.ones_like(y2)
    for ch in (r2, g2, b2):
        dc = ch - y2
        over = ch > 1; under = ch < 0
        k = np.where(over, np.minimum(k, (1 - y2) / np.where(dc == 0, 1, dc)), k)
        k = np.where(under, np.minimum(k, (0 - y2) / np.where(dc == 0, 1, dc)), k)
    k = np.clip(k, 0, 1)
    r2, g2, b2 = ycc_to_rgb(y2, cb * k, cr * k)
    return [np.clip(v, 0, 1) for v in (r2, g2, b2)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--size', type=int, default=33)
    ap.add_argument('--preset', default='v3', choices=sorted(PRESETS))
    a = ap.parse_args()
    p = PRESETS[a.preset]
    n = a.size
    t = np.linspace(0, 1, n)
    # ordre .cube : R varie le plus vite, puis G, puis B
    b, g, r = np.meshgrid(t, t, t, indexing='ij')
    R, G, B = look(r.ravel(), g.ravel(), b.ravel(), p)
    with open(a.out, 'w') as f:
        f.write(f'TITLE "BAD LIFE look {a.preset} BALANCED"\n')
        f.write('# Input/Output: Rec.709 BT.1886, full-range RGB. Generated by tools/make_lut.py\n')
        f.write(f'LUT_3D_SIZE {n}\nDOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n')
        for x in zip(R, G, B):
            f.write('%.6f %.6f %.6f\n' % x)


if __name__ == '__main__':
    main()
