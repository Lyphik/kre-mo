#!/usr/bin/env python3
"""BAD LIFE V5.1 — continuite de luminance du master (complete qc_extract.py et qc_master.py).

Entree : qc_effets.csv du compositeur (colonnes luma_source / luma_sortie, mesurees en 160x90, 0-255).

  1. Variations de luminance a l'interieur d'un plan : pour chaque image (hors 1re image d'un plan),
     residu = d log(sortie) - d log(source). Le traitement etant une LUT fixe par plan, la sortie doit
     suivre la source ; un residu eleve signale un saut introduit par le traitement (effet qui pulse,
     LUT qui change en cours de plan, etc.). Les images de transition musicale et de flash de montage
     (effets volontairement suspendus ou declenches) sont comptees a part.
     Une image au-dessus du seuil est EXPLIQUEE si les effets n'y varient pas (|d effet_moyen| < 0,002)
     et si la sortie bouge dans le meme sens que la source : c'est alors la reponse de la LUT fixe du
     plan (courbe contrastee) a un saut de lumiere present dans la source, pas une instabilite.
     Verdict OK si aucune image au-dessus du seuil n'est inexpliquee.
  2. Fondu de fin : instants ou la luminance passe sous 50 / 25 / 10 % du niveau de depart,
     source contre master (doivent coincider a une image pres).
Usage : qc_luma.py QC_EFFETS.csv PLANS.csv OUT.json [SEUIL=0.06] [FONDU_DEBUT_S=161.7] [FPS=50]
"""
import csv, json, sys
import numpy as np

QE, PLANS, OUTP = sys.argv[1:4]
SEUIL = float(sys.argv[4]) if len(sys.argv) > 4 else 0.06
F_DEB = float(sys.argv[5]) if len(sys.argv) > 5 else 161.7
FPS = float(sys.argv[6]) if len(sys.argv) > 6 else 50.0

rows = list(csv.DictReader(open(QE)))
img = np.array([int(r['image']) for r in rows])
ls = np.array([float(r['luma_source']) for r in rows]); lo = np.array([float(r['luma_sortie']) for r in rows])
tr = np.array([float(r['transition']) for r in rows]); fl = np.array([float(r['flash_montage']) for r in rows])
fam = [r['famille'] for r in rows]
eff = np.array([float(r['effet_moyen']) for r in rows])
starts = sorted(int(r['image_debut']) for r in csv.DictReader(open(PLANS)))
plan_of = np.searchsorted(starts, img, side='right') - 1

d = np.full(len(img), np.nan)
same = (np.diff(img) == 1) & (np.diff(plan_of) == 0)
res = np.diff(np.log(lo + 2.0)) - np.diff(np.log(ls + 2.0))
d[1:][same] = res[same]
vol = (tr > 0) | (fl > 0)
vol[1:] |= vol[:-1].copy()                      # l'image qui suit une transition/flash (retour a la normale)
m_norm = ~np.isnan(d) & ~vol; m_vol = ~np.isnan(d) & vol
over = m_norm & (np.abs(d) > SEUIL)
dsrc = np.zeros(len(img)); dout = np.zeros(len(img)); deff = np.full(len(img), np.inf)
dsrc[1:] = np.diff(ls); dout[1:] = np.diff(lo); deff[1:] = np.abs(np.diff(eff))
expl = over & (deff < 0.002) & (np.sign(dsrc) == np.sign(dout))
rep = {'seuil_residu_log': SEUIL, 'images_analysees': int(m_norm.sum()),
       'residu_p99': round(float(np.percentile(np.abs(d[m_norm]), 99)), 4) if m_norm.any() else None,
       'residu_max': round(float(np.abs(d[m_norm]).max()), 4) if m_norm.any() else None,
       'images_au_dessus_du_seuil': int(over.sum()),
       'dont_expliquees_reponse_LUT_a_un_saut_source': int(expl.sum()),
       'inexpliquees': int((over & ~expl).sum()),
       'detail': [{'image': int(img[k]), 't_s': round(float(img[k] / FPS), 2), 'famille': fam[k], 'residu': round(float(d[k]), 3),
                   'luma_src': [float(ls[k - 1]), float(ls[k])], 'luma_out': [float(lo[k - 1]), float(lo[k])],
                   'effet': [float(eff[k - 1]), float(eff[k])], 'explique': bool(expl[k])} for k in np.nonzero(over)[0][:40]],
       'transitions_et_flashs': {'images': int(m_vol.sum()),
                                 'residu_max': round(float(np.abs(d[m_vol]).max()), 4) if m_vol.any() else None}}
f = img >= round(F_DEB * FPS)
if f.sum() > 10:
    t = img[f] / FPS; a, b = ls[f], lo[f]
    def cross(y, p):
        ref = y[:10].mean(); k = np.nonzero(y < p * ref)[0]
        return round(float(t[k[0]]), 2) if len(k) else None
    rep['fondu_fin'] = {str(p): {'source_s': cross(a, p), 'master_s': cross(b, p)} for p in (0.5, 0.25, 0.10)}
    ok_f = all(v['source_s'] is not None and v['master_s'] is not None and abs(v['source_s'] - v['master_s']) <= 1.0 / FPS + 1e-6
               for v in rep['fondu_fin'].values())
    rep['fondu_fin']['verdict'] = 'OK' if ok_f else 'ECHEC'
rep['verdict'] = 'OK' if (over & ~expl).sum() == 0 and rep.get('fondu_fin', {}).get('verdict', 'OK') == 'OK' else 'A VERIFIER'
json.dump(rep, open(OUTP, 'w'), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in rep.items() if k != 'detail'}, indent=1, ensure_ascii=False))
for x in rep['detail'][:15]: print(x)
