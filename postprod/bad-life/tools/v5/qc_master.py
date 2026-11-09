#!/usr/bin/env python3
"""BAD LIFE V5.1 — controles specifiques du MASTER (complete qc_extract.py).

  1. Audio ORIGINAL copie bit a bit : empreinte SHA-256 des paquets audio (source contre master).
  2. Durees des flux video et audio = 175,200 s ; 8760 images.
  3. Montage intact sur les 8760 images : chaque image du master est plus correlee a l'image source
     de meme indice qu'a ses voisines (+/- 1) -> aucun decalage, aucune image ajoutee ou perdue,
     coupes a leur place. Les images ou la source est quasi fixe (voisines identiques) sont comptees a part.
  4. Coupes : a chaque frontiere de plan validee, la correlation source/master saute comme dans la source.
Usage : qc_master.py SOURCE MASTER.mp4 PLANS.csv OUT.json
"""
import csv, json, subprocess, sys
import numpy as np

SRC, MST, PLANS, OUTP = sys.argv[1:5]
rep = {}


def sh(cmd): return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()


ha = sh(['ffmpeg', '-nostdin', '-v', 'error', '-i', SRC, '-map', '0:a:0', '-c', 'copy', '-f', 'streamhash', '-hash', 'sha256', '-'])
hb = sh(['ffmpeg', '-nostdin', '-v', 'error', '-i', MST, '-map', '0:a:0', '-c', 'copy', '-f', 'streamhash', '-hash', 'sha256', '-'])
rep['audio_bit_a_bit'] = {'source': ha, 'master': hb, 'verdict': 'OK' if ha and ha.split('=')[-1] == hb.split('=')[-1] else 'ECHEC'}
dur = lambda f, s: sh(['ffprobe', '-v', 'error', '-select_streams', s, '-show_entries', 'stream=duration,nb_frames,codec_name', '-of', 'csv=p=0', f])
rep['durees'] = {'video_master': dur(MST, 'v:0'), 'audio_master': dur(MST, 'a:0'), 'video_source': dur(SRC, 'v:0'), 'audio_source': dur(SRC, 'a:0')}
vm = rep['durees']['video_master'].split(','); am_ = rep['durees']['audio_master'].split(',')
rep['durees']['verdict'] = 'OK' if (abs(float(vm[1]) - 175.2) < 0.001 and vm[2] == '8760' and abs(float(am_[1]) - 175.2) < 0.03) else 'ECHEC'


def frames(path, w=160, h=90):
    b = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', path, '-vf', f'scale={w}:{h}:flags=area,format=gray', '-f', 'rawvideo', '-'],
                       capture_output=True).stdout
    a = np.frombuffer(b, np.uint8).reshape(-1, h * w).astype(np.float32)
    a -= a.mean(axis=1, keepdims=True); a /= (np.linalg.norm(a, axis=1, keepdims=True) + 1e-6)
    return a


S, M = frames(SRC), frames(MST)
n = min(len(S), len(M)); rep['images'] = {'source': len(S), 'master': len(M)}
c0 = np.einsum('ij,ij->i', M[:n], S[:n])
cm = np.full(n, -2.0); cp = np.full(n, -2.0)
cm[1:] = np.einsum('ij,ij->i', M[1:n], S[:n - 1]); cp[:-1] = np.einsum('ij,ij->i', M[:n - 1], S[1:n])
static = np.zeros(n, bool)                       # source quasi fixe : voisine identique (25p dans 50p, plan fixe)
static[1:] |= np.einsum('ij,ij->i', S[1:n], S[:n - 1]) > 0.995
static[:-1] |= np.einsum('ij,ij->i', S[:n - 1], S[1:n]) > 0.995
bad = (np.maximum(cm, cp) > c0 + 0.002) & ~static
rep['montage_8760_images'] = {'images_meilleure_correlation_hors_indice': int(bad.sum()), 'images_quasi_fixes_non_decidables': int(static.sum()),
                             'correlation_moyenne_meme_image': round(float(c0.mean()), 4), 'correlation_min_meme_image': round(float(c0.min()), 4),
                             'images_signalees': [int(i) for i in np.nonzero(bad)[0][:20]],
                             'verdict': 'OK' if bad.sum() == 0 and len(S) == len(M) else 'A VERIFIER'}
bounds = [int(r['image_debut']) for r in csv.DictReader(open(PLANS)) if int(r['image_debut']) > 0]
ok_cut = 0; ko = []
for k in bounds:
    if k >= n: continue
    s_jump = float(np.dot(S[k], S[k - 1])); m_jump = float(np.dot(M[k], M[k - 1]))
    if abs(s_jump - m_jump) < 0.15: ok_cut += 1
    else: ko.append((k, round(s_jump, 3), round(m_jump, 3)))
rep['coupes'] = {'frontieres_validees': len(bounds), 'meme_saut_source_master': ok_cut, 'ecarts': ko[:20],
                 'verdict': 'OK' if not ko else 'A VERIFIER'}
rep['VERDICT_MASTER'] = 'CONFORME' if all(rep[k]['verdict'] == 'OK' for k in ('audio_bit_a_bit', 'durees', 'montage_8760_images', 'coupes')) else 'A VERIFIER'
json.dump(rep, open(OUTP, 'w'), indent=1, ensure_ascii=False)
print(json.dumps(rep, indent=1, ensure_ascii=False))
