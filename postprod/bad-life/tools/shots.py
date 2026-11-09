"""Agrege les statistiques signalstats par plan (entre deux coupes detectees). Usage : shots.py DOSSIER"""
import re,sys,json,statistics as st
A=sys.argv[1]
cuts=[float(x) for x in open(A+'/cuts.txt')]
sc=[float(m) for m in re.findall(r'lavfi.scene_score=([0-9.]+)',open(A+'/scenes.txt').read())]
fr=[];cur={}
for l in open(A+'/stats.txt'):
    if l.startswith('frame:'):
        if cur: fr.append(cur)
        cur={'t':float(re.search(r'pts_time:([0-9.]+)',l).group(1))}
    else:
        m=re.match(r'lavfi\.signalstats\.(\w+)=([-0-9.]+)',l)
        if m: cur[m.group(1)]=float(m.group(2))
fr.append(cur)
dur=max(x["t"] for x in fr)+0.02  # fin = derniere image + 1/50 s (source 50 i/s)
b=[0.0]+cuts+[dur]
shots=[]
for i in range(len(b)-1):
    f=[x for x in fr if b[i]<=x['t']<b[i+1]]
    if not f: continue
    g=lambda k: st.mean(x[k] for x in f)
    shots.append(dict(n=i+1,start=round(b[i],2),end=round(b[i+1],2),d=round(b[i+1]-b[i],2),score=round(sc[i-1],2) if i else None,
      yavg=round(g('YAVG'),1),ylow=round(g('YLOW'),1),yhigh=round(g('YHIGH'),1),ymin=round(min(x['YMIN'] for x in f)),ymax=round(max(x['YMAX'] for x in f)),
      sat=round(g('SATAVG'),1),hue=round(g('HUEAVG')),u=round(g('UAVG'),1),v=round(g('VAVG'),1)))
json.dump(shots,open(A+'/shots.json','w'),indent=1)
print('n start  end   dur  score yavg ylow yhigh ymin ymax sat  hue  U     V')
for s in shots: print(f"{s['n']:3} {s['start']:6} {s['end']:6} {s['d']:5} {s['score'] or '-':>5} {s['yavg']:5} {s['ylow']:5} {s['yhigh']:5} {s['ymin']:4} {s['ymax']:4} {s['sat']:5} {s['hue']:4} {s['u']:5} {s['v']:5}")
