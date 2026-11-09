#!/usr/bin/env python3
"""BAD LIFE V5 — compositeur (etalonnage C hybride + effets), un extrait a la fois.

REGLE ABSOLUE (cahier des charges V5, section 2) :
  sortie = alpha * SOURCE + (1 - alpha) * (DECOR etalonne + effets)
  - SOURCE = image originale decodee (RGB 16 bits), JAMAIS modifiee : pas de LUT, pas de nettete,
    pas d'effet, pas de reduction de chroma sur les artistes.
  - alpha = matte RVM normalise (>= 0,97 -> 1) : pixels opaques des artistes = source, verifie
    image par image AVANT le redimensionnement 4K (qc_artistes.csv : ecart max attendu = 0).
  - Le redimensionnement 4K (Lanczos) est applique uniformement a l'image entiere par l'encodeur.

Decor : LUT de la famille du plan (v5_nuit / v5_nuit_ambre / v5_jour). Passages N&B : la chroma du
decor suit la chroma de la source (aucune dominante pendant ces passages). Effets selon la famille,
ponderes par la profondeur (Depth Anything V2) et par la confiance du detourage.

Sorties : <id>_V5_COMPLET.mp4 (4K HEVC), <id>_V5_ETALONNAGE_SEUL.mp4 (4K HEVC),
          <id>_MASQUE.mp4 (1080p, visualisation de la zone protegee), qc_artistes.csv, qc_effets.csv, stills/
Usage : composite_v5.py SOURCE PLANS.csv CONFIG.json MUSIQUE.json MATTE_DIR DEPTH_DIR LUT_DIR EXTRAITS.json ID OUT_DIR
"""
import csv, json, os, subprocess, sys, time
import numpy as np, cv2

SRC, PLANS, CFGP, MUSP, MATTE, DEPTH, LUTDIR, EXTP, EID, OUT = sys.argv[1:11]
cfg = json.load(open(CFGP)); mus = json.load(open(MUSP))
ex = next(e for e in json.load(open(EXTP))['extraits'] if e['id'] == EID)
W, H, FPS = 1920, 1080, 50
F0, F1 = int(round(ex['debut_s'] * FPS)), int(round(ex['fin_s'] * FPS)); NF = F1 - F0
os.makedirs(f'{OUT}/stills', exist_ok=True)
rng = np.random.default_rng(20261109)
STILLS_ONLY = os.environ.get('STILLS_ONLY') == '1'
STILL_EVERY = int(os.environ.get('STILL_EVERY', '60'))

# ---------------- plans, familles, references de chroma ----------------
plans = list(csv.DictReader(open(PLANS)))
for p in plans:
    p['a'], p['b'] = int(p['image_debut']), int(p['image_fin'])
FAMS = cfg['familles']; NOFX = set(cfg['sans_effet'])
# --- options V5.1 (absentes de la config V5 -> comportement V5 inchange) ---
PLAN_OV = {k: v for k, v in cfg.get('plans', {}).items() if not k.startswith('_')}   # cle = image de debut du plan
DUREE_MIN_FX = int(cfg.get('effets_duree_min_images', 0))                          # plans <= N images : sans effet
SUFFIXE = cfg.get('suffixe', 'V5')
ART = cfg.get('artistes', {'mode': 'source'})                                       # 'source' ou 'harmonise'
VIDEO_MASQUE = bool(cfg.get('video_masque', True))
AUDIO_COPIE = bool(cfg.get('audio_copie', False)) and F0 == 0 and abs(NF / FPS - 175.2) < 0.03   # clip entier uniquement


def lut_family(idx):
    """Famille utilisee pour la LUT : plan lui-meme, ou plan reel voisin (precedent) si X / N&B."""
    p = plans[idx]
    if p['famille'] in FAMS: return p['famille']
    if p.get('famille_lut') in FAMS: return p['famille_lut']     # X / N&B : voisin le plus ressemblant
    for d in range(1, 40):
        for j in (idx - d, idx + d):
            if 0 <= j < len(plans) and plans[j]['famille'] in FAMS: return plans[j]['famille']
    return 'A_jour_cite'


fam_ref = {}
for f in FAMS:
    v = [float(p['chroma']) for p in plans if p['famille'] == f and p['micro'] == '0' and float(p['chroma']) > 0]
    fam_ref[f] = float(np.median(v)) if v else 6.0
frame_plan = {}
for k, p in enumerate(plans):
    for i in range(max(p['a'], F0), min(p['b'], F1)): frame_plan[i] = k

# ---------------- confiance du detourage ----------------
qual = {}
qp = f'{MATTE}/qualite.csv'
if os.path.exists(qp):
    for r in csv.DictReader(open(qp)): qual[int(r['image'])] = (float(r['bord_incertain']), float(r['instabilite']))
cc = cfg['confiance_masque']


def confidence(i):
    unc, ins = qual.get(i, (0.0, 0.0))
    c1 = np.clip(1 - (ins - cc['i0']) / cc['di'], cc['min'], 1); c2 = np.clip(1 - (unc - cc['b0']) / cc['db'], cc['min'], 1)
    return float(c1 * c2)


# ---------------- transitions musicales ----------------
secs = mus['sections']; impacts = np.array(mus['impacts_s']); tol = cfg['transitions']['tolerance_s']
TRANS = []
for k in range(1, len(plans)):
    p, q = plans[k - 1], plans[k]
    if not (F0 < q['a'] < F1): continue
    # uniquement entre deux PLANS REELS (>= 0,3 s, hors effets de montage / N&B) : jamais sur un insert
    # d'une image ni dans une salve (sinon deux voiles lumineux a 20 ms d'intervalle)
    if p['micro'] == '1' or q['micro'] == '1' or p['famille'] in NOFX or q['famille'] in NOFX: continue
    fp, fq = lut_family(k - 1), lut_family(k)
    if fp == fq: continue
    tc = q['a'] / FPS
    sec = next((s for s in secs if s['debut_s'] <= tc < s['fin_s']), None)
    forte = bool(sec and sec['intensite'] == 'forte'); near_bnd = any(abs(s['debut_s'] - tc) < 0.3 for s in secs)
    tb = None
    if len(impacts):                                   # regle 1 : impact musical + section forte / frontiere
        ti = float(impacts[np.argmin(np.abs(impacts - tc))])
        if abs(ti - tc) <= tol and (forte or near_bnd): tb = ti
    if tb is None and forte:                           # regle 2 : kick ou snare <= 40 ms dans une section forte
        hits = np.array(mus['kicks_s'] + mus['snares_s'])
        th = float(hits[np.argmin(np.abs(hits - tc))])
        if abs(th - tc) <= 0.04: tb = th
    if tb is not None: TRANS.append((tb, len(TRANS) % 2))


TR_DECAY = float(cfg['transitions'].get('descente_s', 0.14))
TR_JOUR_EXCLU = bool(cfg['transitions'].get('jour_exclu', False))     # V5.1 : pas de voile sur un plan de jour


def trans_env(t):
    e, side = 0.0, 0
    for tb, sd in TRANS:
        v = np.exp(-((t - tb) / 0.05) ** 2) if t < tb else np.exp(-(t - tb) / TR_DECAY)
        if v > e: e, side = v, sd
    return e, side


# ---------------- I/O ----------------
LUTS = sorted({FAMS[lut_family(frame_plan[i])]['lut'] for i in range(F0, F1)})


def decoder(lut=None):
    # Conversions par zscale : la chaine swscale (YUV -> RGB -> YUV 4:2:0) introduisait un decalage de
    # chrominance mesure (V -0,57 unite 8 bits) sur un temoin sans traitement ; zscale : V -0,12, comme
    # le chemin YUV direct (doc 09, chaine de conversion).
    vf = 'zscale=matrixin=709:rangein=limited:transferin=709:primariesin=709,format=gbrp16le'
    if lut: vf += f",lut3d=file='{LUTDIR}/badlife_look_{lut}.cube':interp=tetrahedral"
    vf += ',format=rgb48le'
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{F0 / FPS:.3f}', '-i', SRC, '-t', f'{NF / FPS:.3f}', '-vf', vf,
                             '-f', 'rawvideo', '-'], stdout=subprocess.PIPE, bufsize=W * H * 6)


def encoder_4k(path):
    # RGB brut (sans balise de transfert) : seules la matrice et la plage sont converties ; balises BT.709 ensuite.
    vf = ('format=gbrp16le,zscale=w=3840:h=2160:filter=lanczos,zscale=matrix=709:range=limited,'
          'format=yuv420p10le,setsar=1,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv')
    x265 = 'colorprim=bt709:transfer=bt709:colormatrix=bt709:range=limited:vbv-maxrate=80000:vbv-bufsize=160000:aq-mode=3:log-level=error'
    # Master (clip entier + 'audio_copie') : flux audio ORIGINAL copie bit a bit, sans coupe ni reencodage.
    # Extraits : un extrait ne peut pas etre coupe a l'echantillon pres en copie -> AAC 320 kb/s.
    if AUDIO_COPIE:
        ain = ['-i', SRC]; acod = ['-c:a', 'copy']
    else:
        ain = ['-ss', f'{F0 / FPS:.3f}', '-t', f'{NF / FPS:.3f}', '-i', SRC]; acod = ['-c:a', 'aac', '-b:a', '320k']
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb48le', '-s', f'{W}x{H}', '-r', str(FPS),
                             '-i', '-'] + ain + ['-map', '0:v', '-map', '1:a:0',
                             '-vf', vf, '-c:v', 'libx265', '-preset', 'medium', '-crf', '16', '-profile:v', 'main10', '-tag:v', 'hvc1',
                             '-x265-params', x265] + acod + ['-movflags', '+faststart', path], stdin=subprocess.PIPE)


def encoder_1080(path):
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS),
                             '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)


def read(p):
    b = p.stdout.read(W * H * 6)
    return None if len(b) < W * H * 6 else np.frombuffer(b, np.uint16).reshape(H, W, 3)


def to16(img): return (np.clip(img, 0, 1) * 65535 + 0.5).astype(np.uint16)


def luma(img): return img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def blur(img, sigma, f=4):
    s = cv2.resize(img, (W // f, H // f), interpolation=cv2.INTER_AREA)
    s = cv2.GaussianBlur(s, (0, 0), max(sigma / f, 0.5))
    return cv2.resize(s, (W, H), interpolation=cv2.INTER_LINEAR)


def streak(img, sx, f=4):
    s = cv2.resize(img, (W // f, H // f), interpolation=cv2.INTER_AREA)
    s = cv2.GaussianBlur(s, (0, 0), sigmaX=sx / f, sigmaY=0.6)
    return cv2.resize(s, (W, H), interpolation=cv2.INTER_LINEAR)


def src_chroma(img):
    s = cv2.resize(img, (160, 90), interpolation=cv2.INTER_AREA)
    Y = luma(s); cb = (s[..., 2] - Y) / 1.8556; cr = (s[..., 0] - Y) / 1.5748
    yt = 16 + 219 * Y; mid = (yt > 40) & (yt < 220)
    return float(np.hypot(224 * cb, 224 * cr)[mid].mean()) if mid.mean() > 0.30 else None


# ---------------- profondeur (interpolation entre images cles du meme plan) ----------------
dkeys = sorted(int(f[6:11]) for f in os.listdir(DEPTH) if f.startswith('depth_')) if os.path.isdir(DEPTH) else []


def depth_at(i):
    k = frame_plan[i]; a, b = plans[k]['a'], plans[k]['b']
    ks = [x for x in dkeys if a <= x < b]
    if not ks: return None
    lo = max([x for x in ks if x <= i], default=ks[0]); hi = min([x for x in ks if x >= i], default=ks[-1])
    dl = cv2.imread(f'{DEPTH}/depth_{lo:05d}.png', -1).astype(np.float32) / 65535
    if hi == lo: d = dl
    else:
        dh = cv2.imread(f'{DEPTH}/depth_{hi:05d}.png', -1).astype(np.float32) / 65535
        w = (i - lo) / (hi - lo); d = (1 - w) * dl + w * dh
    return cv2.resize(d, (W, H), interpolation=cv2.INTER_LINEAR)


# ---------------- fumee (bruit fractal 2 couches) ----------------
def fractal_noise(h, w, octaves=5, base=6, seed=0):
    r = np.random.default_rng(seed); acc = np.zeros((h, w), np.float32); amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh, gw = base * 2 ** o, int(base * 2 ** o * w / h)
        acc += amp * cv2.resize(r.random((gh, gw), dtype=np.float32), (w, h), interpolation=cv2.INTER_CUBIC); tot += amp; amp *= 0.5
    acc /= tot; return (acc - acc.min()) / (acc.max() - acc.min())


NS = 4; NH, NW = 2 * H // NS, 2 * W // NS
N_FAR, N_NEAR, N_EVO = fractal_noise(NH, NW, seed=11), fractal_noise(NH, NW, seed=23), fractal_noise(NH, NW, 3, 3, seed=37)


def layer(field, ox, oy):
    x0 = int(np.clip(W / 2 + ox, 0, W)) // NS; y0 = int(np.clip(H / 2 + oy, 0, H)) // NS
    return field[y0:y0 + H // NS, x0:x0 + W // NS]


def smoke(t, cam, strength):
    # cam = -(deplacement du contenu). La fenetre d'echantillonnage recule de k * deplacement pour que le
    # motif suive le decor (k = 0,6 au fond, 1,15 devant : parallaxe). ERRATUM : V4 et premiers rendus V5
    # utilisaient le signe oppose (fumee se deplacant a l'inverse du decor lors des mouvements de camera).
    far = layer(N_FAR, -14 * t + 0.6 * cam[0], 4 * t + 0.6 * cam[1]); near = layer(N_NEAR, -30 * t + 1.15 * cam[0], -6 * t + 1.15 * cam[1])
    evo = layer(N_EVO, 8 * t, -10 * t)
    n = (0.55 * far + 0.45 * near) * (0.75 + 0.5 * evo)
    d = cv2.resize(smoothstep(0.34, 0.86, n).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    return np.clip(d * strength, 0, 1)


class Particles:
    def __init__(s, n):
        s.x = rng.uniform(-0.25 * W, 1.25 * W, n).astype(np.float32); s.y = rng.uniform(-0.1 * H, 1.1 * H, n).astype(np.float32)
        s.z = (rng.uniform(0.1, 1.0, n) ** 0.7).astype(np.float32); s.vy = -rng.uniform(5, 18, n).astype(np.float32)
        s.ph = rng.uniform(0, 2 * np.pi, n).astype(np.float32); s.fq = rng.uniform(0.25, 0.7, n).astype(np.float32)

    def render(s, t, cam, light, disp, twinkle=True, jmap=None, jseuil=0.0):
        lay = [np.zeros((H, W), np.float32) for _ in range(3)]
        px = s.x + 9 * np.sin(0.6 * t + s.ph) * s.z - cam[0] * (0.6 + 0.7 * s.z)
        py = (s.y + s.vy * t * s.z - cam[1] * (0.6 + 0.7 * s.z) + 0.1 * H) % (1.2 * H) - 0.1 * H
        tw = 0.65 + 0.35 * np.sin(2 * np.pi * s.fq * t + s.ph) if twinkle else np.full(len(px), 0.85, np.float32)
        for k in range(len(px)):
            x, y = int(px[k]), int(py[k])
            if not (0 <= x < W and 0 <= y < H): continue
            if disp is not None and s.z[k] < disp[y, x] - 0.08: continue      # cachee par le decor plus proche
            # V5.1 : particule SUPPRIMEE (pas attenuee) si elle n'est pas dans l'influence d'une vraie source
            # lumineuse du decor (halo ou faisceau) -> plus de points repartis uniformement sur l'image
            if jmap is not None and jmap[y, x] < jseuil: continue
            b = float(tw[k] * (0.3 + 1.1 * light[y, x]))
            bk = 0 if s.z[k] < 0.45 else (1 if s.z[k] < 0.8 else 2)
            cv2.circle(lay[bk], (x, y), 1 + int(round(4 * s.z[k] ** 2)), b, -1, cv2.LINE_AA)
        return cv2.GaussianBlur(lay[0], (0, 0), 0.8) + cv2.GaussianBlur(lay[1], (0, 0), 1.4) + 0.8 * cv2.GaussianBlur(lay[2], (0, 0), 3.0)


class Cam:
    def __init__(s): s.prev = None; s.acc = np.zeros(2, np.float32); s.win = cv2.createHanningWindow((480, 270), cv2.CV_32F)
    def reset(s): s.prev = None; s.acc[:] = 0

    def update(s, img, prot):
        L = luma(img); g = cv2.resize(L * (1 - prot) + L.mean() * prot, (480, 270), interpolation=cv2.INTER_AREA)
        if s.prev is not None:
            (dx, dy), resp = cv2.phaseCorrelate(s.prev, g, s.win)
            if resp > 0.08 and abs(dx) < 20 and abs(dy) < 20: s.acc += np.array([dx, dy], np.float32) * 4
        s.prev = g; return -s.acc


def radial_blur(img, cx, cy, steps=12, k=0.032, f=2):
    s = cv2.resize(img, (W // f, H // f), interpolation=cv2.INTER_AREA); acc = s.copy()
    for st in range(1, steps + 1):
        sc = 1 - k * st; M = np.float32([[sc, 0, (1 - sc) * cx / f], [0, sc, (1 - sc) * cy / f]])
        acc += cv2.warpAffine(s, M, (W // f, H // f), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    return cv2.resize(acc / (steps + 1), (W, H), interpolation=cv2.INTER_LINEAR)


BL = {'rouge': np.array([1.0, 0.16, 0.12], np.float32), 'ambre': np.array([1.0, 0.55, 0.22], np.float32)}
xx = np.arange(W, dtype=np.float32)[None, :]; yy = np.arange(H, dtype=np.float32)[:, None]

# ---------------- boucle ----------------
dec_src = decoder(None); dec = {l: decoder(l) for l in LUTS}
dec_subj = decoder(ART['lut']) if ART.get('mode') == 'harmonise' else None    # LUT GLOBALE des artistes (V5.1)
enc = {} if STILLS_ONLY else {'COMPLET': encoder_4k(f'{OUT}/{EID}_{SUFFIXE}_COMPLET.mp4'),
                               'ETAL': encoder_4k(f'{OUT}/{EID}_{SUFFIXE}_ETALONNAGE_SEUL.mp4')}
if not STILLS_ONLY and VIDEO_MASQUE: enc['MASK'] = encoder_1080(f'{OUT}/{EID}_MASQUE.mp4')
qa = csv.writer(open(f'{OUT}/qc_artistes.csv', 'w', newline='')); qa.writerow(['image', 'plan', 'famille', 'px_opaques', 'ecart_max_vs_source', 'reference'])
CNAMES = ['fumee', 'rayons', 'contre_jour', 'particules', 'halos', 'halation', 'anamorphique']
qe = csv.writer(open(f'{OUT}/qc_effets.csv', 'w', newline='')); qe.writerow(['image', 'famille', 'confiance', 'chroma_k', 'effet_moyen', 'transition'] + CNAMES + ['flash_montage', 'gain_effets', 'luma_source', 'luma_sortie'])
cam = Cam(); parts = None; a_prev = None; curp = None; conf_s = 1.0; fxg = 1.0; bl_prev = None; bl2 = None; rays_s = None; key_s = None; src_mode = None; presence = 0.0; scol_s = None; cam_prev_off = np.zeros(2, np.float32); t0 = time.time()
for n in range(NF):
    i = F0 + n
    S16 = read(dec_src); Dl = {l: read(p) for l, p in dec.items()}
    SL16 = read(dec_subj) if dec_subj is not None else None
    if S16 is None or any(v is None for v in Dl.values()) or (dec_subj is not None and SL16 is None): print('fin de flux', n); break
    k = frame_plan[i]; p = plans[k]; fam = p['famille']; lf = lut_family(k); P = FAMS[lf]
    if str(p['a']) in PLAN_OV: P = dict(P, **PLAN_OV[str(p['a'])])          # V5.1 : reglages propres au plan
    t = (i - p['a']) / FPS
    if k != curp:
        curp = k; cam.reset(); parts = Particles(int(P.get('particules_n', 300) * max(P['particules'], 0.01))); a_prev = None; bl_prev = None; bl2 = None; rays_s = None; key_s = None; src_mode = None; presence = 0.0; scol_s = None
        cam_prev_off = np.zeros(2, np.float32)
    SRCf = S16.astype(np.float32) / 65535; D = Dl[P['lut']].astype(np.float32) / 65535
    a = cv2.imread(f'{MATTE}/alpha_{i:05d}.png', 0).astype(np.float32) / 255
    if a_prev is not None: a = 0.75 * a + 0.25 * a_prev
    a_prev = a; a = np.clip(a / 0.97, 0, 1); am = a[..., None]
    prot = np.clip(cv2.GaussianBlur(cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19))), (0, 0), 3), 0, 1)
    # chroma du decor suit la source (passages N&B, fondu) — jamais appliquee aux artistes
    # Passages N&B / rampes : poids w de la chroma etalonnee ; (1 - w) = chroma EXACTE de la source.
    # w = 0 sous le seuil N&B (3,0, meme mesure que build_shots), 1 au-dessus de 80 % de la reference
    # de la famille. Applique au decor ET aux effets (apres effets) : aucune teinte ne peut apparaitre.
    c = src_chroma(SRCf); ref = 0.8 * fam_ref.get(lf, 6.0)
    kc = 1.0 if c is None else float(smoothstep(3.0, max(ref, 3.5), c))
    SRCc = SRCf - luma(SRCf)[..., None]

    def chroma_src_mix(img):
        if kc >= 0.999: return img
        g = luma(img)[..., None]
        return g + kc * (img - g) + (1 - kc) * SRCc

    # ARTISTES : mode 'source' = pixels source exacts ; mode 'harmonise' (V5.1) = meme LUT globale tres legere
    # pour chaque pixel (aucune retouche locale), dosee par 'force', chroma N&B identique a la source.
    if SL16 is not None:
        SUBJ = SRCf + float(ART.get('force', 1.0)) * (SL16.astype(np.float32) / 65535 - SRCf)
        SUBJ = chroma_src_mix(SUBJ)
    else:
        SUBJ = SRCf
    if P.get('artistes_mode') == 'source': SUBJ = SRCf     # master : fondu de fin, artistes = pixels source
    ETAL = am * SUBJ + (1 - am) * chroma_src_mix(D)      # D reste brut pour les effets (melange une seule fois)
    COMP = {}
    def _acc(name, before):
        COMP[name] = COMP.get(name, 0.0) + float(np.abs(DC - before).mean())
    DC = D.copy(); efx = fam not in NOFX and any(P[x] > 0 for x in ('fumee', 'particules', 'halos', 'rayons'))
    if (p['b'] - p['a']) <= DUREE_MIN_FX: efx = False   # V5.1 : inserts de 1-2 images -> aucun effet procedural
    # FLASH DU MONTAGE : image nettement plus claire que la mediane de son plan (salve surexposee du
    # monteur) -> effets suspendus (fondu rapide) pour ne pas pulser avec le flash ni s'y superposer.
    ylum = float(luma(cv2.resize(SRCf, (160, 90), interpolation=cv2.INTER_AREA)).mean()) * 255
    flash = ylum > 1.30 * float(p['luma']) + 12
    fxg = (0.4 * fxg + 0.6 * (0.0 if flash else 1.0)) if n else (0.0 if flash else 1.0)
    conf_s = 0.9 * conf_s + 0.1 * confidence(i) if n else confidence(i)
    camoff = cam.update(ETAL, prot)
    if efx:
        LD = luma(D); light = np.clip(blur(LD, 45) * 2.4, 0, 1)
        disp = depth_at(i); far = 1 - disp if disp is not None else np.full((H, W), 0.5, np.float32)
        key_raw = smoothstep(0.74, 0.98, LD) * smoothstep(0.06, 0.26, LD - blur(LD, 25, 2)) * (1 - a)
        # lissage temporel COMPENSE EN MOUVEMENT : la carte precedente est recalee sur le deplacement
        # camera avant moyenne -> halos stables, qui suivent la source sans trainer
        if key_s is None: key_s = key_raw
        else:
            dmv = camoff - cam_prev_off
            key_s = 0.6 * cv2.warpAffine(key_s, np.float32([[1, 0, -dmv[0]], [0, 1, -dmv[1]]]), (W, H), borderMode=cv2.BORDER_CONSTANT) + 0.4 * key_raw
        cam_prev_off = camoff.copy()
        key = key_s
        near_src = np.clip(blur(key, 60) * 3, 0, 1)
        dens = None
        if P['fumee'] > 0:
            if P.get('fumee_profondeur') == 'loin':
                # V5.1 : brume RESERVEE au lointain (decor proche net, fond qui recule = profondeur lisible)
                dens = smoke(i / FPS, camoff, P['fumee'] * conf_s) * smoothstep(0.30, 0.85, far)
            else:
                dens = smoke(i / FPS, camoff, P['fumee'] * conf_s) * (0.35 + 0.65 * far)
            col = np.array(P['fumee_couleur'], np.float32)[None, None, :] * (1 - near_src[..., None] * P['ambre_sources']) \
                + np.array([0.95, 0.55, 0.22], np.float32) * near_src[..., None] * P['ambre_sources']
            dm = dens[..., None]
            _b = DC; DC = DC * (1 - 0.30 * dm) + col * (0.45 + 1.2 * light)[..., None] * dm * 0.5; _acc('fumee', _b)
        rays = None
        if P['rayons'] > 0 and dens is not None:
            # Source des rayons VERROUILLEE par plan : mode 'lampe' (source du decor) choisi des qu'une
            # source est vue ; sinon, apres 8 images, mode 'sujet' (contre-jour). Jamais de bascule en
            # cours de plan : si la source n'est plus vue, les rayons s'estompent (fondu), sans saut.
            m = (key > 0.3).astype(np.uint8); nlab, lab, st, cen = cv2.connectedComponentsWithStats(m)
            lamps = [np.array([cen[j][0], cen[j][1]], np.float32) for j in range(1, nlab)]
            areas = [st[j, cv2.CC_STAT_AREA] for j in range(1, nlab)]
            subj = None
            if P['contre_jour']:
                mm = (a > 0.5).astype(np.uint8); n2, _, st2, _ = cv2.connectedComponentsWithStats(mm)
                if n2 > 1:
                    k2 = 1 + int(np.argmax(st2[1:, cv2.CC_STAT_AREA])); subj = np.array([st2[k2, 0] + st2[k2, 2] / 2, st2[k2, 1] + 0.28 * st2[k2, 3]], np.float32)
            if src_mode is None:
                if lamps: src_mode = 'lampe'; bl_prev = lamps[int(np.argmax(areas))]
                elif subj is not None and (i - p['a']) >= 8 and P.get('rayons_source', 'toutes') != 'lampe': src_mode = 'sujet'; bl_prev = subj
                if src_mode is not None and (i - p['a']) <= 2: presence = 1.0   # source visible des la coupe
            seen = False
            if src_mode == 'lampe' and lamps and bl_prev is not None:
                dist = [np.linalg.norm(l - bl_prev) for l in lamps]; j = int(np.argmin(dist))
                if dist[j] < 0.12 * W: bl_prev = 0.85 * bl_prev + 0.15 * lamps[j]; seen = True
            elif src_mode == 'sujet' and subj is not None:
                bl_prev = 0.85 * bl_prev + 0.15 * subj; seen = True
            presence = 0.9 * presence + 0.1 * (1.0 if seen else 0.0)
            if bl_prev is not None and presence > 0.02:
                cx, cy = float(bl_prev[0]), float(bl_prev[1])
                # couleur de la source : MOYENNE sur une zone de 61 px (image floutee), lissee dans le temps.
                # (V5 rendu 1 : lue sur un seul pixel -> scintillement des rayons, image 2373 de l'extrait 5)
                y0_, y1_ = int(np.clip(cy - 30, 0, H - 1)), int(np.clip(cy + 31, 1, H))
                x0_, x1_ = int(np.clip(cx - 30, 0, W - 1)), int(np.clip(cx + 31, 1, W))
                zc = D[y0_:y1_, x0_:x1_].reshape(-1, 3).mean(axis=0) if (y1_ > y0_ and x1_ > x0_) else np.ones(3, np.float32)
                zc = 0.5 * zc / (zc.max() + 1e-3) + 0.5 * (BL[P['contre_jour']] if P['contre_jour'] else np.array([1.0, 0.6, 0.3], np.float32))
                scol_s = zc if scol_s is None else 0.9 * scol_s + 0.1 * zc
                scol = scol_s
                rays = radial_blur(dens * (0.4 + light), cx, cy) * P['rayons'] * conf_s * presence
                if os.environ.get('DEBUG_RAYS'):
                    print(f'DBG {i} mode={src_mode} vu={seen} pres={presence:.2f} cx={cx:.0f} cy={cy:.0f} brut={float(rays.mean())*1000:.2f} nlampes={len(lamps)}', flush=True)
                rays_s = rays if rays_s is None else 0.65 * rays_s + 0.35 * rays   # lissage temporel (par plan)
                rays = rays_s
                _b = DC; DC = DC + (rays * 0.5)[..., None] * scol; _acc('rayons', _b)
        if P['contre_jour'] and P['contre_jour_force'] > 0:
            mm = (a > 0.5).astype(np.uint8); n2, _, st2, _ = cv2.connectedComponentsWithStats(mm)
            if n2 > 1:
                k2 = 1 + int(np.argmax(st2[1:, cv2.CC_STAT_AREA])); x0, y0, w0, h0 = st2[k2, :4]
                tg = np.array([x0 + w0 / 2, y0 + 0.28 * min(h0, H - y0), max(h0, 200)], np.float32)
                bl2 = tg if bl2 is None else 0.85 * bl2 + 0.15 * tg      # remis a zero a chaque plan
                cx, cy, hh = bl2; sg = 0.42 * hh
                fall = np.exp(-(((xx - cx) ** 2) / (2 * (0.75 * sg) ** 2) + ((yy - cy) ** 2) / (2 * sg ** 2))).astype(np.float32)
                _b = DC; DC = DC + (fall * P['contre_jour_force'] * conf_s * (0.3 + 0.7 * (1 - LD)))[..., None] * BL[P['contre_jour']]; _acc('contre_jour', _b)
        if P['particules'] > 0:
            plight = light if rays is None else np.clip(light + 1.5 * rays, 0, 1)
            jmap = None
            if P.get('particules_justifiees'):
                jmap = np.clip(near_src + (0 if rays is None else 2.0 * rays), 0, 1)
            pl = parts.render(t, camoff, plight, disp, twinkle=P.get('particules_scintillement', True),
                              jmap=jmap, jseuil=P.get('particules_seuil_source', 0.25)) * 0.85 * P['particules'] * conf_s
            pcol = 0.55 * np.array([1.0, 0.82, 0.62], np.float32) + 0.45 * np.clip(blur(D, 30) * 2.5, 0, 1)
            _b = DC; DC = DC + pl[..., None] * pcol; _acc('particules', _b)
        if P['halos'] > 0 or P['halation'] > 0 or P['anamorphique'] > 0:
            keyf = key * smoothstep(0.45, 0.75, key) if P.get('sources_persistantes') else key   # V5.1 : sources stables seulement
            if P.get('sources_marge_bord', 0) > 0:
                # V5.1 : une source en lisiere du cadre (qui entre / sort pendant un mouvement de camera) ne
                # declenche pas de halo ni de flare : sinon l'effet 'pulse' en quelques images (extrait 1, 4184-4191)
                mb = P['sources_marge_bord']
                edge = smoothstep(0.0, mb * W, np.minimum(xx, W - 1 - xx)) * smoothstep(0.0, mb * H, np.minimum(yy, H - 1 - yy))
                keyf = keyf * edge
            kcol = D * keyf[..., None]
            if P['halos'] > 0:
                _b = DC; DC = DC + (0.55 * blur(kcol, 8, 2) + 0.40 * blur(kcol, 24) + 0.30 * blur(kcol, 64)) * 0.7 * P['halos']; _acc('halos', _b)
            if P['halation'] > 0:
                _b = DC; DC = DC + blur(luma(kcol), 12, 2)[..., None] * np.array([1.0, 0.42, 0.22], np.float32) * 0.45 * P['halation']; _acc('halation', _b)
            if P['anamorphique'] > 0:
                k2 = keyf * smoothstep(0.15, 0.30, LD - blur(LD, 40, 2))
                st_ = streak(luma(D) * k2, 110)
                _b = DC; DC = DC + st_[..., None] * np.array([1.0, 0.50, 0.30], np.float32) * 1.6 * P['anamorphique']; _acc('anamorphique', _b)
    if fxg < 0.999: DC = D + fxg * (DC - D)
    e, side = trans_env(i / FPS)
    if TR_JOUR_EXCLU and lf in ('A_jour_cite', 'OUTRO_fondu'): e = 0.0
    if e > 0.01:
        gx = (1 - xx / W) if side == 0 else (xx / W)
        band = np.exp(-((yy - H * 0.45) / (H * 0.18)) ** 2)
        DC = DC + ((gx ** 2.0) * (0.35 + 0.65 * band) * e * cfg['transitions']['force'])[..., None] * np.array([1.0, 0.45, 0.20], np.float32)
    DC = chroma_src_mix(DC)                            # effets colores neutralises pendant le N&B
    OUTF = am * SUBJ + (1 - am) * DC
    O16, E16 = to16(OUTF), to16(ETAL)
    opq = a >= 1.0
    # reference des artistes : la source (mode 'source') ou la source passee par la LUT globale (mode
    # 'harmonise'). Ecart 0 = aucune retouche locale ni aucun effet sur les pixels opaques des artistes.
    REF16 = S16 if SL16 is None else to16(SUBJ)
    dmax = int(np.abs(O16.astype(np.int32) - REF16.astype(np.int32))[opq].max()) if opq.any() else 0
    dmax_e = int(np.abs(E16.astype(np.int32) - REF16.astype(np.int32))[opq].max()) if opq.any() else 0
    qa.writerow([i, p['plan'], fam, int(opq.sum()), max(dmax, dmax_e), 'source' if (SL16 is None or P.get('artistes_mode') == 'source') else 'source+LUT_globale'])
    qe.writerow([i, fam, round(conf_s, 3), round(kc, 3), round(float(np.abs(OUTF - ETAL).mean()), 5), round(e, 3)] + [round(COMP.get(c, 0.0), 5) for c in CNAMES] + [int(flash), round(fxg, 3),
                round(ylum, 2), round(float(luma(cv2.resize(OUTF, (160, 90), interpolation=cv2.INTER_AREA)).mean()) * 255, 2)])
    if not STILLS_ONLY:
        enc['COMPLET'].stdin.write(O16.tobytes()); enc['ETAL'].stdin.write(E16.tobytes())
        ov = (np.clip(SRCf[..., ::-1], 0, 1) * 255).astype(np.uint8)
        tint = ov.copy(); tint[..., 1] = np.clip(tint[..., 1].astype(np.int32) + 90, 0, 255).astype(np.uint8)
        ovm = (ov * (1 - am * 0.55) + tint * am * 0.55).astype(np.uint8)
        if 'MASK' in enc: enc['MASK'].stdin.write(ovm.tobytes())
    if n % STILL_EVERY == 0 or n == NF // 2:
        for tag, im in (('SRC', SRCf), ('ETAL', ETAL), ('V5', OUTF)):
            cv2.imwrite(f'{OUT}/stills/{tag}_{i:05d}.png', (np.clip(im[..., ::-1], 0, 1) * 65535).astype(np.uint16))
    if (n + 1) % 50 == 0: print(f'{EID} {n + 1}/{NF} images, {(n + 1) / (time.time() - t0):.2f} i/s', flush=True)
for p_ in enc.values(): p_.stdin.close()
for p_ in enc.values(): p_.wait()
print('TERMINE', EID, 'LUT:', LUTS, 'transitions:', TRANS)
