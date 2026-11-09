#!/usr/bin/env python3
"""BAD LIFE V5.1 — controles specifiques du MASTER (complete qc_extract.py).

  1. Audio ORIGINAL copie bit a bit : empreinte SHA-256 des paquets audio (source contre master).
  2. Durees des flux video et audio = 175,200 s ; 8760 images.
  3. Montage intact sur les 8760 images : aucune image du master n'est plus correlee a une image source
     d'un autre indice (fenetre +/- 3) qui differe reellement de la sienne -> aucun decalage, aucune image
     ajoutee ou perdue, coupes a leur place. Seules les images quasi uniformes (noir) sont non decidables.
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
    sd = a.std(axis=1)
    a -= a.mean(axis=1, keepdims=True); a /= (np.linalg.norm(a, axis=1, keepdims=True) + 1e-6)
    return a, sd


(S, sdS), (M, _) = frames(SRC), frames(MST)
n = min(len(S), len(M)); rep['images'] = {'source': len(S), 'master': len(M)}
c0 = np.einsum('ij,ij->i', M[:n], S[:n])
# Fenetre +/- 3 images : une image du master est fausse si elle ressemble davantage a une image source
# d'un autre indice ET que cette image source est reellement differente de la sienne (corr < 0,995).
# Les doublons 25p dans 50p (images source identiques) ne sont donc plus exclus mais neutres.
uni = sdS[:n] < 2.0                              # image quasi uniforme (noir) : correlation non definie
bad = np.zeros(n, bool); wrong_to = {}
for o in (-3, -2, -1, 1, 2, 3):
    i = np.arange(max(0, -o), min(n, n - o)); j = i + o
    cj = np.einsum('ij,ij->i', M[i], S[j]); sij = np.einsum('ij,ij->i', S[i], S[j])
    hit = (cj > c0[i] + 0.002) & (sij < 0.995)
    bad[i[hit]] = True
    for k in i[hit]: wrong_to.setdefault(int(k), o)
bad &= ~uni
rep['montage_8760_images'] = {'images_meilleure_correlation_hors_indice': int(bad.sum()), 'images_uniformes_non_decidables': int(uni.sum()),
                             'images_uniformes_indices': [int(i) for i in np.nonzero(uni)[0][:40]],
                             'correlation_moyenne_meme_image': round(float(c0[~uni].mean()), 4), 'correlation_min_meme_image_hors_uniformes': round(float(c0[~uni].min()), 4),
                             'images_signalees': [(int(i), wrong_to[int(i)], round(float(c0[i]), 3)) for i in np.nonzero(bad)[0][:20]],
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
