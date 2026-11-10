#!/usr/bin/env python3
"""BAD LIFE — controle du teaser de sortie (doc 12 §12.8).

  1. Format : 1080x1920, 50 i/s, 1500 images, 30,000 s, H.264, AAC ; departs video et audio a 0.
  2. Artistes : qc_teaser.csv (ecart max sortie / master recadre sur les pixels d'artistes, avant encodage) = 0
     hors transition d'ouverture.
  3. Son : correlation croisee du son du teaser avec l'extrait original (hors fondus) : decalage 0 attendu.
  4. Ecrans noirs : aucune image quasi noire hors ouverture au noir (0-0,8 s).
  5. Scintillement : sauts de luminance image a image a l'interieur d'un segment, hors coupes et eclairs
     volontaires, rapportes a la variation de la source au meme instant.
Usage : qc_teaser.py TEASER.mp4 SOURCE EDL.json QC_TEASER.csv OUT.json [PLANS.csv]
"""
import csv, json, subprocess, sys
import numpy as np

TZ, SRC, EDLP, QCC, OUTP = sys.argv[1:6]
E = json.load(open(EDLP)); FPS = E['fps']; TA = E['audio_debut_s']; DUR = E['duree_s']; NF = int(round(DUR * FPS))
rep = {}; ok = True


def probe(path, sel):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', sel, '-count_frames', '-show_entries',
                        'stream=codec_name,profile,width,height,r_frame_rate,nb_read_frames,start_time,duration,sample_rate,channels',
                        '-of', 'json', path], capture_output=True, text=True)
    return json.loads(r.stdout)['streams'][0]


v = probe(TZ, 'v:0'); a = probe(TZ, 'a:0')
fmt_ok = (v['codec_name'] == 'h264' and v['width'] == 1080 and v['height'] == 1920 and v['r_frame_rate'] == f'{FPS}/1'
          and int(v['nb_read_frames']) == NF and abs(float(v['duration']) - DUR) < 1e-3 and a['codec_name'] == 'aac'
          and abs(float(a['duration']) - DUR) < 0.03 and float(v['start_time']) == 0 and abs(float(a['start_time'])) < 1e-3)
rep['format'] = {'video': f"{v['codec_name']} {v.get('profile')} {v['width']}x{v['height']} {v['r_frame_rate']} {v['nb_read_frames']} img {v['duration']} s, depart {v['start_time']}",
                 'audio': f"{a['codec_name']} {a.get('sample_rate')} Hz {a.get('channels')} can. {a['duration']} s, depart {a['start_time']}",
                 'verdict': 'OK' if fmt_ok else 'ECHEC'}
ok &= fmt_ok

rows = list(csv.DictReader(open(QCC)))
strict = [r for r in rows if r['controle'] == 'strict']
dmax = max(int(r['ecart_max_artistes_vs_master']) for r in strict)
rep['artistes'] = {'images': len(rows), 'images_strictes': len(strict), 'images_transition_ouverture': len(rows) - len(strict),
                   'px_artistes_moyen_par_image': int(np.mean([int(r['px_artistes']) for r in rows])),
                   'ecart_max_vs_master_recadre': dmax, 'verdict': 'OK' if dmax == 0 and len(rows) == NF else 'ECHEC'}
ok &= dmax == 0 and len(rows) == NF


def pcm(path, ss=None, t=None):
    cmd = ['ffmpeg', '-v', 'error'] + (['-ss', f'{ss:.4f}'] if ss is not None else []) + ['-i', path] + (['-t', f'{t:.4f}'] if t else []) + \
          ['-map', '0:a:0', '-ac', '1', '-ar', '8000', '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32)


x = pcm(TZ); y = pcm(SRC, TA, DUR)
n = min(len(x), len(y)); a0, a1 = int(1.0 * 8000), int(28.5 * 8000)          # hors fondus
xs, ys = x[a0:a1] - x[a0:a1].mean(), y[a0:a1] - y[a0:a1].mean()
lags = range(-80, 81)
cc = [float(np.dot(xs[max(0, l):len(xs) + min(0, l)], ys[max(0, -l):len(ys) - max(0, l)])) for l in lags]
best = list(lags)[int(np.argmax(cc))]
corr = float(np.dot(xs, ys) / (np.linalg.norm(xs) * np.linalg.norm(ys) + 1e-9))
rep['son'] = {'decalage_echantillons_8kHz': best, 'decalage_ms': best / 8.0, 'correlation_a_decalage_0': round(corr, 4),
              'verdict': 'OK' if best == 0 and corr > 0.98 else 'ECHEC'}
ok &= best == 0 and corr > 0.98


def luma(path, w=108, h=192):
    b = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'scale={w}:{h}:flags=area,format=gray', '-f', 'rawvideo', '-'],
                       capture_output=True).stdout
    return np.frombuffer(b, np.uint8).reshape(-1, h, w).astype(np.float32)


L = luma(TZ); m = L.mean(axis=(1, 2)); t = np.arange(len(m)) / FPS
fs = E.get('fondu_sortie_video'); t_fin = fs['de'] if fs else DUR + 1
t_deb = E.get('fondu_entree_video', 0.8)
noirs = [int(i) for i in np.nonzero((m < 6) & (t >= t_deb) & (t < t_fin))[0]]
rep['ecrans_noirs'] = {'seuil_luma_moyenne': 6, 'images_noires_hors_fondus': len(noirs), 'premieres': noirs[:10],
                       'luma_min_hors_fondus': round(float(m[(t >= t_deb) & (t < t_fin)].min()), 1), 'verdict': 'OK' if not noirs else 'ECHEC'}
ok &= not noirs

cut_f = {int(round(s['t0'] * FPS)) for s in E['segments']}
# coupes d'origine a l'interieur des segments cales (salves du montage du clip) : changement de plan source
PL = sys.argv[6] if len(sys.argv) > 6 else None
if PL:
    import bisect
    st = sorted(int(r['image_debut']) for r in csv.DictReader(open(PL)))
    srcs = [int(r['image_source']) for r in rows]
    pid = [bisect.bisect(st, x) for x in srcs]
    cut_f |= {i for i in range(1, len(pid)) if pid[i] != pid[i - 1]}
volont = set()
for c in cut_f:
    volont |= set(range(c - 1, c + 7))                                     # coupe + eclair de lumiere (decroissance 0,12 s)
td = int(round(E['textes']['disponible']['de'] * FPS)); volont |= set(range(td - 1, td + 12))
for k, v in E['textes'].items():                                                       # apparitions et sorties de textes
    for cle in ('de', 'de2', 'a'):
        if cle in v: tk = int(round(v[cle] * FPS)); volont |= set(range(tk - 20, tk + 16))
volont |= set(range(int(round(t_fin * FPS)) - 1, NF))                                   # fondu de sortie
d2 = np.zeros(len(m)); d2[1:-1] = np.abs(m[1:-1] - 0.5 * (m[:-2] + m[2:]))
cand = [i for i in range(1, len(m) - 1) if i not in volont and t_deb <= t[i] < t_fin]
worst = max(cand, key=lambda i: d2[i]) if cand else None
rep['scintillement'] = {'methode': 'ecart de luminance moyenne a la tendance (2e difference), codes 0-255, hors coupes, eclairs et apparitions de textes',
                        'max': round(float(d2[worst]), 2) if worst is not None else 0, 'image': worst,
                        'images_au_dessus_de_4_codes': [int(i) for i in cand if d2[i] > 4][:20]}
# image signalee EXPLIQUEE si la source a, au meme instant, un saut relatif au moins moitie aussi fort (eclair d'origine)
srcs_ = [int(r['image_source']) for r in rows]
def lsrc(i):
    b = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{i / FPS:.4f}', '-i', SRC, '-frames:v', '1', '-vf', 'scale=192:108:flags=area,format=gray',
                        '-f', 'rawvideo', '-'], capture_output=True).stdout
    return float(np.frombuffer(b, np.uint8).mean())
det = []
for i in rep['scintillement']['images_au_dessus_de_4_codes']:
    a_, b_, c_ = (lsrc(srcs_[k]) for k in (i - 1, i, i + 1))
    rs = abs(b_ - 0.5 * (a_ + c_)) / max(b_, 1); rt = d2[i] / max(m[i], 1)
    det.append({'image': i, 't_s': round(i / FPS, 2), 'image_source': srcs_[i], 'saut_relatif_teaser': round(rt, 3), 'saut_relatif_source': round(rs, 3),
                'explique_par_la_source': bool(rs >= 0.5 * rt)})
rep['scintillement']['detail'] = det
rep['scintillement']['verdict'] = 'OK' if all(x['explique_par_la_source'] for x in det) else 'A VERIFIER'
tx = [r for r in rows if r.get('texte_x_min', '') != '']
if tx:
    xmin = min(int(r['texte_x_min']) for r in tx); xmax = max(int(r['texte_x_max']) for r in tx)
    ymin = min(int(r['texte_y_min']) for r in tx); ymax = max(int(r['texte_y_max']) for r in tx)
    tok = xmin >= 40 and xmax <= 1080 - 40 and ymin >= 100 and ymax <= 1650
    rep['textes'] = {'images_avec_texte': len(tx), 'emprise_x': [xmin, xmax], 'emprise_y': [ymin, ymax],
                     'regle': 'lettres a 40 px au moins des bords, entre y=100 et y=1650 (zones sures Reels / TikTok / Shorts)',
                     'verdict': 'OK' if tok else 'ECHEC'}
    ok &= tok
rep['VERDICT'] = 'CONFORME' if ok and rep['scintillement']['verdict'] == 'OK' else 'A VERIFIER'
json.dump(rep, open(OUTP, 'w'), indent=1, ensure_ascii=False)
print(json.dumps(rep, indent=1, ensure_ascii=False))
