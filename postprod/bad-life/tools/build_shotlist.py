#!/usr/bin/env python3
"""Construit data/shots.csv (table des plans) a partir de shots.json (analyse) et data/families.json.
Usage : build_shotlist.py ANALYSE/shots.json data/families.json data/shots.csv"""
import csv, json, sys, statistics as st
shots = json.load(open(sys.argv[1])); fam = json.load(open(sys.argv[2]))
rows = []
for s in shots:
    n = str(s['n'])
    f = fam['shots'].get(n) or ('micro_plan_flash' if s['d'] < 0.5 else 'NON_CLASSE')
    rows.append(dict(plan=n, debut_s=s['start'], fin_s=s['end'], duree_s=s['d'], famille=f,
                     y_moy=s['yavg'], y_p10=s['ylow'], y_p90=s['yhigh'], y_min=s['ymin'], y_max=s['ymax'],
                     sat_moy=s['sat'], note=fam.get('notes', {}).get(n, '')))
with open(sys.argv[3], 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print('famille                 plans  duree_s  Ymoy[min-max]      Yp10 moy  Ymin moy  Ymax max  sat moy')
for f in sorted({r['famille'] for r in rows}):
    g = [r for r in rows if r['famille'] == f]
    ys = [r['y_moy'] for r in g]
    print(f"{f:22} {len(g):5} {sum(r['duree_s'] for r in g):8.2f}  {st.mean(ys):5.1f} [{min(ys):5.1f}-{max(ys):5.1f}]  {st.mean(r['y_p10'] for r in g):8.1f}  {st.mean(r['y_min'] for r in g):8.1f}  {max(r['y_max'] for r in g):8}  {st.mean(r['sat_moy'] for r in g):6.1f}")
