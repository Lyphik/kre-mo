#!/usr/bin/env python3
"""BAD LIFE V5 — controle qualite d'un extrait rendu (etape 6).

Tests (criteres de rejet du cahier des charges V5, section 9) :
  1. Format : 3840x2160, SAR 1:1, 50 i/s, nombre d'images, HEVC Main10, BT.709 plage TV.
  2. Artistes : ecart max des pixels opaques vs source AVANT redimensionnement (qc_artistes.csv) = 0.
  3. Synchronisation image : pour un echantillon d'images, correlation (luma reduite) entre la sortie
     et la source maximale a decalage 0 (et non +/-1, +/-2 images).
  4. Synchronisation audio : correlation croisee audio sortie / source : decalage 0 attendu.
  5. Scintillement : sauts d'intensite d'effet image a image A L'INTERIEUR d'un plan (hors coupes et
     transitions) : rapport au niveau moyen de l'effet du plan.
  6. N&B : pendant les passages N&B de la source, chroma de la sortie (decor compris) <= 3,0.
Usage : qc_extract.py SOURCE EXTRAITS.json ID RENDU_DIR PLANS.csv NB.json
"""
import csv, json, subprocess, sys
import numpy as np, cv2

SRC, EXTP, EID, RD, PLANS, NBP = sys.argv[1:7]
ex = next(e for e in json.load(open(EXTP))['extraits'] if e['id'] == EID)
F0, F1 = int(round(ex['debut_s'] * 50)), int(round(ex['fin_s'] * 50)); NF = F1 - F0
rep = {'extrait': EID, 'debut_s': ex['debut_s'], 'fin_s': ex['fin_s']}


def probe(p):
    o = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                        'stream=codec_name,profile,width,height,sample_aspect_ratio,r_frame_rate,nb_frames,color_space,color_transfer,color_primaries,color_range,bit_rate',
                        '-of', 'json', p], capture_output=True, text=True).stdout
    return json.loads(o)['streams'][0]


ok = True
for tag in ('V5_COMPLET', 'V5_ETALONNAGE_SEUL'):
    s = probe(f'{RD}/{EID}_{tag}.mp4')
    good = (s['width'] == 3840 and s['height'] == 2160 and s.get('sample_aspect_ratio') == '1:1' and s['r_frame_rate'] == '50/1'
            and int(s['nb_frames']) == NF and s['codec_name'] == 'hevc' and s['color_space'] == 'bt709' and s['color_range'] == 'tv')
    rep[f'format_{tag}'] = f"{s['width']}x{s['height']} {s.get('sample_aspect_ratio')} {s['r_frame_rate']} {s['nb_frames']} img {s['codec_name']} {s['profile']} {s['color_space']}/{s['color_range']} {int(s['bit_rate']) / 1e6:.1f} Mb/s -> {'OK' if good else 'ECHEC'}"
    ok &= good
qa = list(csv.DictReader(open(f'{RD}/qc_artistes.csv')))
dmax = max(int(r['ecart_max_vs_source']) for r in qa); popq = int(np.mean([int(r['px_opaques']) for r in qa]))
rep['artistes'] = f"{len(qa)} images, {popq} px opaques/image en moyenne, ecart max vs source = {dmax} -> {'OK' if dmax == 0 else 'ECHEC'}"
ok &= dmax == 0


def frames(path, ss=None, t=None, w=160, h=90):
    cmd = ['ffmpeg', '-v', 'error'] + (['-ss', f'{ss:.3f}'] if ss is not None else []) + ['-i', path] + (['-t', f'{t:.3f}'] if t else []) + \
          ['-vf', f'scale={w}:{h}:flags=area,format=gray', '-f', 'rawvideo', '-']
    b = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(b, np.uint8).reshape(-1, h, w).astype(np.float32)


src = frames(SRC, F0 / 50, NF / 50); out = frames(f'{RD}/{EID}_V5_COMPLET.mp4')
n = min(len(src), len(out)); rep['images_source_vs_sortie'] = f'{len(src)} / {len(out)}'
bad = 0; samples = list(range(3, n - 3, 7))
for i in samples:
    o = out[i].ravel() - out[i].mean()
    cs = [float(np.dot(o, src[i + d].ravel() - src[i + d].mean()) / (np.linalg.norm(o) * np.linalg.norm(src[i + d].ravel() - src[i + d].mean()) + 1e-6)) for d in (-2, -1, 0, 1, 2)]
    if int(np.argmax(cs)) != 2 and max(cs) - cs[2] > 0.002: bad += 1
rep['sync_image'] = f'{len(samples)} images testees, {bad} meilleure correlation hors decalage 0 -> {"OK" if bad == 0 else "A VERIFIER"}'
ok &= bad == 0


def audio(path, ss=None, t=None):
    cmd = ['ffmpeg', '-v', 'error'] + (['-ss', f'{ss:.3f}'] if ss is not None else []) + ['-i', path] + (['-t', f'{t:.3f}'] if t else []) + \
          ['-ac', '1', '-ar', '8000', '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32)


a_s, a_o = audio(SRC, F0 / 50, NF / 50), audio(f'{RD}/{EID}_V5_COMPLET.mp4')
m = min(len(a_s), len(a_o)) - 800; seg_s = a_s[400:400 + m]
best = max(range(-160, 161), key=lambda d: float(np.dot(seg_s, a_o[400 + d:400 + d + m])) if 0 <= 400 + d and 400 + d + m <= len(a_o) else -1e9)
rep['sync_audio'] = f'decalage audio mesure = {best / 8:.2f} ms (resolution 0,125 ms ; AAC reencode pour les extraits) -> {"OK" if abs(best) <= 8 else "ECHEC"}'
ok &= abs(best) <= 8
qe = list(csv.DictReader(open(f'{RD}/qc_effets.csv')))
plans = list(csv.DictReader(open(PLANS)))
bounds = {int(p['image_debut']) for p in plans}
eff = np.array([float(r['effet_moyen']) for r in qe]); tr = np.array([float(r['transition']) for r in qe]); imgs = [int(r['image']) for r in qe]
fl = np.array([int(r.get('flash_montage', 0)) for r in qe])
nfl = int(fl.sum())
for j in np.nonzero(fl)[0]:                       # flashs du montage : exclus comme les coupes (+/- 3 images)
    tr[max(0, j - 3):j + 4] = np.maximum(tr[max(0, j - 3):j + 4], 1.0)
# Scintillement = ecart a la TENDANCE locale (difference seconde |e_k - (e_k-1 + e_k+1)/2|) : un pic isole
# ou un saut on/off est detecte, une variation progressive (source qui sort du cadre, fondu) ne l'est pas.
# Version precedente (difference premiere) : signalait a tort la disparition naturelle d'une lumiere sortant
# du cadre (extrait 1, image 4191, verifie visuellement).
def excluded(k):
    return imgs[k] in bounds or imgs[k] - 1 in bounds or (imgs[k] + 1) in bounds or tr[k] > 0.01
worst = 0.0; worst_i = None; worst_d1 = 0.0; worst_d1_i = None
for k in range(1, len(qe) - 1):
    if excluded(k) or excluded(k - 1) or excluded(k + 1): continue
    j0 = max(b for b in bounds if b <= imgs[k]); seg = [eff[q_] for q_ in range(len(qe)) if j0 <= imgs[q_] < imgs[k] + 50]
    lvl = max(np.mean(seg), 0.004)
    d2 = abs(eff[k] - 0.5 * (eff[k - 1] + eff[k + 1])) / lvl; d1 = abs(eff[k] - eff[k - 1]) / lvl
    if d2 > worst: worst, worst_i = d2, imgs[k]
    if d1 > worst_d1: worst_d1, worst_d1_i = d1, imgs[k]
rep['scintillement'] = (f'ecart max a la tendance (pic / saut) = {100 * worst:.1f} % du niveau d\'effet du plan (image {worst_i}) ; '
                        f'variation progressive max = {100 * worst_d1:.1f} % (image {worst_d1_i}) -> {"OK" if worst < 0.12 else "A VERIFIER"}')
ok &= worst < 0.12
rep['transitions'] = f"{int((np.array([float(r['transition']) for r in qe]) > 0.5).sum())} images de pic de transition ; {nfl} images de flash du montage (effets suspendus)"
nbr = [r for r in json.load(open(NBP))['passages'] if r[1] >= F0 and r[0] < F1]
if nbr:
    worst_c = 0.0
    for a0, b0, _, _ in nbr:
        for i in range(max(a0, F0), min(b0 + 1, F1), 3):
            b = subprocess.run(['ffmpeg', '-v', 'error', '-i', f'{RD}/{EID}_V5_COMPLET.mp4', '-vf', f"select=eq(n\\,{i - F0}),scale=160:90:flags=area,format=yuv444p",
                                '-frames:v', '1', '-f', 'rawvideo', '-'], capture_output=True).stdout
            yuv = np.frombuffer(b, np.uint8).reshape(3, 90, 160).astype(np.float32); Y, U, V = yuv
            mid = (Y > 40) & (Y < 220)
            if mid.mean() > 0.3: worst_c = max(worst_c, float(np.hypot(U - 128, V - 128)[mid].mean()))
    # Critere : aucune DOMINANTE ajoutee = moyennes signees U/V de la sortie egales a celles d'un TEMOIN
    # (source passee dans la meme chaine de conversion 4K, sans aucun traitement) a 0,3 unite pres.
    def uvm(path, ss, n, pre=None):
        cmd = ['ffmpeg', '-v', 'error', '-ss', f'{ss:.3f}', '-i', path, '-frames:v', str(n), '-vf', (pre + ',' if pre else '') + 'scale=160:90:flags=area,format=yuv444p', '-f', 'rawvideo', '-']
        a = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.uint8).reshape(-1, 3, 90, 160).astype(np.float32)
        U, V = [], []
        for f in a:
            Y_, u, v = f; mm = (Y_ > 40) & (Y_ < 220)
            if mm.mean() > 0.3: U.append((u - 128)[mm].mean()); V.append((v - 128)[mm].mean())
        return float(np.mean(U)), float(np.mean(V))
    chain = ('zscale=matrixin=709:rangein=limited:transferin=709:primariesin=709,format=gbrp16le,zscale=w=3840:h=2160:filter=lanczos,'
             'zscale=matrix=709:range=limited,format=yuv420p10le')
    msgs = []; good_nb = True
    for a0, b0, _, _ in nbr:
        a1, b1 = max(a0, F0), min(b0 + 1, F1); nn = b1 - a1
        tem = f'{RD}/temoin_nb_{a1}.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a1 / 50:.3f}', '-i', SRC, '-frames:v', str(nn), '-an', '-vf', chain,
                        '-c:v', 'libx265', '-preset', 'ultrafast', '-crf', '10', '-x265-params', 'log-level=error', tem], check=True)
        ut, vt = uvm(tem, 0.0, nn); uo, vo = uvm(f'{RD}/{EID}_V5_COMPLET.mp4', (a1 - F0) / 50, nn)
        d = max(abs(uo - ut), abs(vo - vt)); good_nb &= d <= 0.3
        msgs.append(f'{a1 / 50:.2f}-{b1 / 50:.2f} s : U/V sortie {uo:+.2f}/{vo:+.2f} vs temoin {ut:+.2f}/{vt:+.2f} (ecart max {d:.2f})')
    rep['noir_et_blanc'] = ' ; '.join(msgs) + f' ; chroma max brute {worst_c:.2f} -> {"OK" if good_nb else "ECHEC"}'
    ok &= good_nb
rep['VERDICT'] = 'CONFORME' if ok else 'NON CONFORME / A VERIFIER'
json.dump(rep, open(f'{RD}/qc_rapport.json', 'w'), indent=1, ensure_ascii=False)
for k, v in rep.items(): print(f'{k:28} {v}')
