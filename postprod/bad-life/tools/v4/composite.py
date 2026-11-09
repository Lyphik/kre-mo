#!/usr/bin/env python3
"""BAD LIFE V4 — compositeur des tests A / B / C (un seul passage, base commune).

  A = etalonnage v4 : LUT 'sujets' sur les personnes, LUT 'decor' ailleurs, melange par le matte RVM.
  B = A + atmosphere : fumee rouge volumetrique, particules / poussieres lumineuses (parallaxe par
      profondeur, suivi du mouvement camera), uniquement derriere les personnes.
  C = B + lumiere : halos autour des lumieres existantes, contre-jour derriere les artistes,
      rayons dans la fumee, transitions lumineuses calees sur les temps forts de la musique.

Regle de protection : les effets sont ajoutes a la seule plaque decor, puis l'artiste est recompose
par-dessus avec son matte exact : sortie = matte * sujet + (1 - matte) * (decor + effets). Les pixels des artistes ne sont jamais eclaircis ni modifies par un effet. Controle chiffre :
difference A/B/C mesuree sur le coeur du matte et journalisee (qc_personnes.csv).

Usage : composite.py SOURCE CONFIG.json MATTE_DIR BEATS.json LUT_DECOR LUT_SUJETS OUT_DIR
"""
import csv, json, os, subprocess, sys, time
import numpy as np, cv2

SRC, CFGP, MATTE, BEATSP, LUT_D, LUT_S, OUT = sys.argv[1:8]
cfg = json.load(open(CFGP)); beats = json.load(open(BEATSP))
W, H, FPS = 1920, 1080, cfg['fps']
SS, DUR = cfg['source_start_s'], cfg['duration_s']
NF = int(round(DUR * FPS))
os.makedirs(OUT, exist_ok=True); os.makedirs(f'{OUT}/stills', exist_ok=True)
rng = np.random.default_rng(20261109)          # graine fixe : rendu reproductible
STILLS = {30, 100, 175, 220, 300, 345, 420, 480, 560, 620}
STILLS_ONLY = os.environ.get('STILLS_ONLY') == '1'   # verification rapide : pas d'encodage


def shot_of(i):
    for s in cfg['shots']:
        if s['f0'] <= i < s['f1']:
            return s
    raise ValueError(i)


# ---------- 1. decodage : deux flux etalonnes (decor / sujets), gain d'exposition par plan ----------
def decoder(lut):
    gains = [s for s in cfg['shots'] if abs(s['exposure'] - 1.0) > 1e-6]
    vf = 'scale=in_color_matrix=bt709:in_range=tv,format=rgb48le'
    for s in gains:
        g = s['exposure']
        vf += (f",lutrgb=r='clip(val*{g},0,maxval)':g='clip(val*{g},0,maxval)':b='clip(val*{g},0,maxval)'"
               f":enable='between(n,{s['f0']},{s['f1'] - 1})'")
    vf += f",format=gbrp16le,lut3d=file='{lut}':interp=tetrahedral,format=rgb48le"
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(SS), '-i', SRC, '-t', str(DUR), '-vf', vf,
                             '-f', 'rawvideo', '-'], stdout=subprocess.PIPE, bufsize=W * H * 6)


def encoder(path):
    vf = ('scale=3840:2160:flags=lanczos+accurate_rnd+full_chroma_int,setsar=1,'
          'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p10le,'
          'setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv')
    x265 = 'colorprim=bt709:transfer=bt709:colormatrix=bt709:range=limited:vbv-maxrate=80000:vbv-bufsize=160000:aq-mode=3:log-level=error'
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb48le', '-s', f'{W}x{H}',
                             '-r', str(FPS), '-i', '-', '-ss', str(SS), '-t', str(DUR), '-i', SRC,
                             '-map', '0:v', '-map', '1:a:0', '-vf', vf, '-c:v', 'libx265', '-preset', 'medium',
                             '-crf', '16', '-profile:v', 'main10', '-tag:v', 'hvc1', '-x265-params', x265,
                             '-c:a', 'aac', '-b:a', '320k', '-movflags', '+faststart', path],
                            stdin=subprocess.PIPE)


def read(p):
    b = p.stdout.read(W * H * 6)
    if len(b) < W * H * 6:
        return None
    return np.frombuffer(b, np.uint16).reshape(H, W, 3).astype(np.float32) / 65535.0


def write(p, img):
    p.stdin.write((np.clip(img, 0, 1) * 65535 + 0.5).astype(np.uint16).tobytes())


def luma(img):
    return img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722


def blur_lowres(img, sigma, f=4):
    """Flou gaussien large calcule en basse resolution (rapide, sans difference visible pour un halo)."""
    small = cv2.resize(img, (W // f, H // f), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), sigma / f)
    return cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ---------- 2. champs de bruit pour la fumee (2 couches de profondeur, 2x la taille de l'image) ----------
def fractal_noise(h, w, octaves=5, base=6, seed=0):
    r = np.random.default_rng(seed); acc = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        gh, gw = base * 2 ** o, int(base * 2 ** o * w / h)
        g = r.random((gh, gw), dtype=np.float32)
        acc += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC); tot += amp; amp *= 0.5
    acc /= tot
    return (acc - acc.min()) / (acc.max() - acc.min())


NOISE_SCALE = 4                                  # bruit calcule a 1/4 de la resolution
NH, NW = 2 * H // NOISE_SCALE, 2 * W // NOISE_SCALE
SMOKE_FAR = fractal_noise(NH, NW, seed=11)
SMOKE_NEAR = fractal_noise(NH, NW, seed=23)
SMOKE_EVOL = fractal_noise(NH, NW, octaves=3, base=3, seed=37)


def sample_layer(field, ox, oy):
    """Fenetre de la taille de l'image (basse res) decalee de (ox, oy) pixels pleine resolution."""
    x0 = int(np.clip(W / 2 + ox, 0, W)) // NOISE_SCALE; y0 = int(np.clip(H / 2 + oy, 0, H)) // NOISE_SCALE
    return field[y0:y0 + H // NOISE_SCALE, x0:x0 + W // NOISE_SCALE]


def smoke_density(t, cam, strength):
    # couche lointaine : derive lente, parallaxe 0.6 ; couche proche : derive rapide, parallaxe 1.15
    far = sample_layer(SMOKE_FAR, -14 * t - 0.6 * cam[0], 4 * t - 0.6 * cam[1])
    near = sample_layer(SMOKE_NEAR, -32 * t - 1.15 * cam[0], -6 * t - 1.15 * cam[1])
    evo = sample_layer(SMOKE_EVOL, 8 * t, -10 * t)
    n = 0.55 * far + 0.45 * near
    n = n * (0.75 + 0.5 * evo)                   # evolution lente des volutes
    d = smoothstep(0.36, 0.88, n)
    d = cv2.resize(d.astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    d *= 0.45 + 0.55 * yy                         # plus dense pres du sol
    return np.clip(d * strength, 0, 1)


# ---------- 3. particules (par plan, positions 3D, parallaxe et derive) ----------
class Particles:
    def __init__(self, n=240):
        self.x = rng.uniform(-0.25 * W, 1.25 * W, n).astype(np.float32)
        self.y = rng.uniform(-0.1 * H, 1.1 * H, n).astype(np.float32)
        self.z = rng.uniform(0.15, 1.0, n).astype(np.float32) ** 0.7
        self.vy = -rng.uniform(5, 18, n).astype(np.float32)
        self.ph = rng.uniform(0, 2 * np.pi, n).astype(np.float32)
        self.fq = rng.uniform(0.25, 0.7, n).astype(np.float32)   # scintillement lent (< 1 Hz)

    def render(self, t, cam, light):
        layer = [np.zeros((H, W), np.float32) for _ in range(3)]
        px = self.x + 9 * np.sin(0.6 * t + self.ph) * self.z - cam[0] * (0.6 + 0.7 * self.z)
        py = self.y + self.vy * t * self.z - cam[1] * (0.6 + 0.7 * self.z)
        py = (py + 0.1 * H) % (1.2 * H) - 0.1 * H
        tw = 0.65 + 0.35 * np.sin(2 * np.pi * self.fq * t + self.ph)
        for k in range(len(px)):
            x, y = int(px[k]), int(py[k])
            if not (0 <= x < W and 0 <= y < H):
                continue
            b = float(tw[k] * (0.35 + 1.0 * light[y, x]))
            bucket = 0 if self.z[k] < 0.45 else (1 if self.z[k] < 0.8 else 2)
            r = 1 + int(round(4 * self.z[k] ** 2))
            cv2.circle(layer[bucket], (x, y), r, b, -1, cv2.LINE_AA)
        out = cv2.GaussianBlur(layer[0], (0, 0), 0.8) + cv2.GaussianBlur(layer[1], (0, 0), 1.4) \
            + 0.8 * cv2.GaussianBlur(layer[2], (0, 0), 3.0)           # proches : bokeh flou
        return out


# ---------- 4. suivi du mouvement camera (correlation de phase sur le decor) ----------
class CamTracker:
    def __init__(self):
        self.prev = None; self.acc = np.zeros(2, np.float32)
        self.win = cv2.createHanningWindow((480, 270), cv2.CV_32F)

    def reset(self):
        self.prev = None; self.acc[:] = 0

    def update(self, img, protect):
        g = cv2.resize(luma(img) * (1 - protect) + luma(img).mean() * protect, (480, 270), interpolation=cv2.INTER_AREA)
        if self.prev is not None:
            (dx, dy), resp = cv2.phaseCorrelate(self.prev, g, self.win)
            if resp > 0.08 and abs(dx) < 20 and abs(dy) < 20:
                self.acc += np.array([dx, dy], np.float32) * 4   # en pixels 1080p
        self.prev = g
        return -self.acc                                          # deplacement a appliquer aux couches


def radial_blur(img, cx, cy, steps=10, k=0.035, f=2):
    small = cv2.resize(img, (W // f, H // f), interpolation=cv2.INTER_AREA); acc = small.copy()
    for s in range(1, steps + 1):
        sc = 1 - k * s
        M = np.float32([[sc, 0, (1 - sc) * cx / f], [0, sc, (1 - sc) * cy / f]])
        acc += cv2.warpAffine(small, M, (W // f, H // f), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    return cv2.resize(acc / (steps + 1), (W, H), interpolation=cv2.INTER_LINEAR)


BACKLIGHT_COL = {'rouge': np.array([1.0, 0.16, 0.12], np.float32), 'ambre': np.array([1.0, 0.55, 0.22], np.float32)}
SMOKE_COL = np.array([0.78, 0.07, 0.06], np.float32)

# transitions : uniquement sur une coupe qui CHANGE D'AMBIANCE (famille differente) et qui tombe
# a moins de 100 ms d'un temps fort de la musique (sobriete BALANCED).
strong = beats['attaques_fortes_s']
TRANS = []
for prev, nxt in zip(cfg['shots'][:-1], cfg['shots'][1:]):
    if prev['famille'] == nxt['famille']:
        continue
    c = nxt['f0'] / FPS
    near = min(strong, key=lambda b: abs(b - c))
    if abs(near - c) <= 0.10:
        TRANS.append((near, len(TRANS) % 2))


def transition_env(t):
    e = 0.0; side = 0
    for tb, sd in TRANS:
        v = np.exp(-((t - tb) / 0.05) ** 2) if t < tb else np.exp(-(t - tb) / 0.12)
        if v > e:
            e, side = v, sd
    return e, side


# ---------- 4bis. intentions N&B du montage : saturation de la source image par image ----------
# Le montage contient des rampes couleur -> N&B -> couleur (ex. plan 28b). La LUT ne doit pas les
# 'recolorer'. On mesure SATAVG de la source par image ; si elle chute sous 80 % de la saturation de
# reference du plan (90e percentile), la chroma de la sortie (effets compris) est reduite d'autant.
def source_saturation():
    out = subprocess.run(['ffmpeg', '-v', 'info', '-nostats', '-ss', str(SS), '-i', SRC, '-t', str(DUR), '-an',
                          '-vf', 'signalstats,metadata=print:key=lavfi.signalstats.SATAVG', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    v = [float(l.split('=')[1]) for l in out.splitlines() if 'SATAVG=' in l]
    return np.array(v[:NF], np.float32)


SRC_SAT = source_saturation()
CHROMA_K = np.ones(NF, np.float32)
for _s in cfg['shots']:
    seg = SRC_SAT[_s['f0']:_s['f1']]
    ref = float(np.percentile(seg, 90)) if len(seg) else 1.0
    CHROMA_K[_s['f0']:_s['f1']] = np.clip(seg / max(0.8 * ref, 1e-3), 0, 1)


def apply_chroma_k(img, k):
    if k >= 0.999:
        return img
    g = luma(img)[..., None]
    return g + k * (img - g)


# ---------- 5. boucle principale ----------
dec_d, dec_s = decoder(LUT_D), decoder(LUT_S)
enc = {} if STILLS_ONLY else {k: encoder(f'{OUT}/BADLIFE_V4_TEST_{k}.mp4') for k in 'ABC'}
cam = CamTracker(); parts = None; a_prev = None; bl_prev = None; cur = None
xx = np.arange(W, dtype=np.float32)[None, :]; yy = np.arange(H, dtype=np.float32)[:, None]
qc = open(f'{OUT}/qc_personnes.csv', 'w', newline=''); qw = csv.writer(qc)
qw.writerow(['image', 'plan', 'px_coeur', 'max_abs_B_A', 'max_abs_C_A', 'moy_abs_C_A', 'px_opaque', 'max_abs_C_A_opaque', 'max_abs_B_A_opaque'])
t0 = time.time()
for i in range(NF):
    D, P = read(dec_d), read(dec_s)
    if D is None or P is None:
        print('fin de flux anticipee', i); break
    s = shot_of(i); t = (i - s['f0']) / FPS
    if s is not cur:                                   # nouveau plan : remise a zero des etats
        cur = s; cam.reset(); parts = Particles(); a_prev = None; bl_prev = None
    a = cv2.imread(f'{MATTE}/alpha_{i:05d}.png', 0).astype(np.float32) / 255.0
    if a_prev is not None:
        a = 0.75 * a + 0.25 * a_prev                   # lissage temporel leger (anti-scintillement des bords)
    a_prev = a
    # normalisation : alpha >= 0.97 -> 1 (echelle lineaire, pas de cassure). Le coeur des artistes
    # devient strictement opaque : aucun effet ne peut y apparaitre, meme a 1 %.
    a = np.clip(a / 0.97, 0, 1)
    am = a[..., None]
    # protection elargie : sert UNIQUEMENT au suivi camera (ignorer les personnes) ; les effets, eux,
    # sont composites DERRIERE les artistes avec le matte exact (pas de liseré, pas de trou).
    protect = np.clip(cv2.GaussianBlur(cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19))), (0, 0), 3), 0, 1)

    # A : etalonnage v4  (sujets sur decor)
    A = am * P + (1 - am) * D
    camoff = cam.update(A, protect)
    LD = luma(D)
    light = np.clip(blur_lowres(LD, 45) * 2.4, 0, 1)    # eclairement local du decor

    # B : atmosphere ajoutee a la plaque decor
    DB = D.copy(); dens = None
    if s['smoke'] > 0:
        dens = smoke_density(i / FPS, camoff, 0.75 * s['smoke'])
        tint = blur_lowres(D, 60)
        tint = tint / (luma(tint)[..., None] + 0.05)
        col = SMOKE_COL * 0.7 + 0.3 * np.clip(tint * 0.35, 0, 1)
        lit = (0.45 + 1.1 * light)[..., None]
        dm = dens[..., None]
        DB = DB * (1 - 0.28 * dm) + col * lit * dm * 0.42
    if s['particles'] > 0:
        pl = parts.render(t, camoff, light) * 0.9 * s['particles']
        pcol = 0.55 * np.array([1.0, 0.82, 0.62], np.float32) + 0.45 * np.clip(blur_lowres(D, 30) * 2.5, 0, 1)
        DB = DB + pl[..., None] * pcol
    B = am * P + (1 - am) * DB

    # C : lumiere ajoutee a la plaque decor (+ atmosphere)
    DC = DB.copy()
    if s['halos'] > 0:
        key = smoothstep(0.80, 0.96, LD) * smoothstep(0.08, 0.25, LD - blur_lowres(LD, 25, 2))
        key = key * (1 - a)                                # seules les lumieres du decor emettent
        kc = D * key[..., None]
        glow = 0.55 * blur_lowres(kc, 8, 2) + 0.40 * blur_lowres(kc, 24) + 0.30 * blur_lowres(kc, 64)
        DC = DC + glow * 0.9 * s['halos']
    if s['backlight']:
        m = (a > 0.5).astype(np.uint8)
        n, lab, st, cen = cv2.connectedComponentsWithStats(m)
        if n > 1:
            k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
            x0, y0, w0, h0 = st[k, 0], st[k, 1], st[k, 2], st[k, 3]
            target = np.array([x0 + w0 / 2, y0 + 0.28 * min(h0, H - y0), max(h0, 200)], np.float32)
            bl_prev = target if bl_prev is None else 0.85 * bl_prev + 0.15 * target
        if bl_prev is not None:
            cx, cy, hh = bl_prev
            sig = 0.42 * hh
            fall = np.exp(-(((xx - cx) ** 2) / (2 * (0.75 * sig) ** 2) + ((yy - cy) ** 2) / (2 * sig ** 2))).astype(np.float32)
            colb = BACKLIGHT_COL[s['backlight']]
            amt = 0.14 if s['backlight'] == 'rouge' else 0.09
            DC = DC + (fall * amt * (0.3 + 0.7 * (1 - LD)))[..., None] * colb
            if dens is not None:                           # rayons volumetriques dans la fumee
                rays = radial_blur(dens * fall, cx, cy)
                DC = DC + (rays * 0.45)[..., None] * colb
    e, side = transition_env(i / FPS)
    if e > 0.01:
        g = (1 - xx / W) if side == 0 else (xx / W)
        leak = (g ** 2.2) * (0.6 + 0.4 * (1 - yy / H))
        DC = DC + (leak * e * 0.55)[..., None] * np.array([1.0, 0.42, 0.18], np.float32)
    C = am * P + (1 - am) * DC

    kc = float(CHROMA_K[i])
    A, B, C = apply_chroma_k(A, kc), apply_chroma_k(B, kc), apply_chroma_k(C, kc)

    # QC : coeur des personnes (matte > 0.98, erode) -> A, B, C doivent etre identiques
    core = cv2.erode((a > 0.98).astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
    opq = a >= 1.0                                   # pixels strictement opaques (artistes)
    if core.any():
        dB = np.abs(B - A)[core]; dC = np.abs(C - A)[core]
        oC = np.abs(C - A)[opq].max() if opq.any() else 0.0
        oB = np.abs(B - A)[opq].max() if opq.any() else 0.0
        qw.writerow([i, s['plan'], int(core.sum()), f'{dB.max():.6f}', f'{dC.max():.6f}', f'{dC.mean():.7f}',
                     int(opq.sum()), f'{oC:.6f}', f'{oB:.6f}'])
    else:
        qw.writerow([i, s['plan'], 0, '', '', '', int(opq.sum()), '', ''])

    for k, img in (('A', A), ('B', B), ('C', C)):
        if not STILLS_ONLY:
            write(enc[k], img)
        if i in STILLS:
            cv2.imwrite(f'{OUT}/stills/{k}_{i:04d}.png', (np.clip(img[..., ::-1], 0, 1) * 65535).astype(np.uint16))
    if i in STILLS:
        cv2.imwrite(f'{OUT}/stills/matte_{i:04d}.png', (a * 255).astype(np.uint8))
    if STILLS_ONLY and i >= max(STILLS) and not os.environ.get('QC_FULL'):
        break
    if (i + 1) % 25 == 0:
        print(f'{i + 1}/{NF} images, {(i + 1) / (time.time() - t0):.2f} i/s', flush=True)

qc.close()
for p in enc.values():
    p.stdin.close()
for p in enc.values():
    p.wait()
print('TERMINE', 'transitions:', TRANS, '| images a chroma reduite (intention N&B):', int((CHROMA_K < 0.999).sum()))
