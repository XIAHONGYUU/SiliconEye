"""AI-inspected tiny MOS: source/drain search relative to observed gate bar, not stale body box."""
from pathlib import Path
import json,copy
import cv2,numpy as np
from shapely.geometry import Polygon
from silicon_eye.geometry_reconstruction import object_polygon
b=Path('benchmarks/ct-full-frame-remaining-v1');p=Path('benchmarks/ct-lower-middle-mos-revision-v2');rd=lambda p:json.loads(Path(p).read_text())
def wr(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
mat=rd(p/'material-model-v1.json');ps={g['id']:g for g in mat['objects']};aas={a['id']:a for a in mat['AA_objects']};raw=rd(b/'all-proposed-with-SD-recovery-v1.json')['objects'];selected=rd(b/'selected-contacts-v1.json')['objects'];gray=cv2.imread('data/test_chip/tile_full/poly.jpg',0);sm=cv2.GaussianBlur(gray,(5,5),1).astype(float);res=sm-cv2.GaussianBlur(sm,(0,0),4);extra=[];audit=[]
for gid,side in [('G65-P04','bottom'),('G65-P08','bottom'),('G66-P07','top')]:
 g=ps[gid];aid=g['AA_target'];a=object_polygon(aas[aid]);l,t,r,bt=a.bounds;gc=[o for o in selected if o.get('POLY_target')==gid];native=np.array([o['source_evidence']['native_center'] for o in gc]);barx,bary=np.median(native,axis=0);entry=dict(gate_id=gid,AA_id=aid,source_gate_bar_center=[float(barx),float(bary)],side=side,source_locator='observed gate-bar anchor; old native box not imposed as material boundary',columns=[]);measured=[]
 for label,sx,lx in [('left',barx-27,l+4),('right',barx+27,r-4)]:
  xl=int(sx)-14;xr=int(sx)+15;yt=int(bary)-48 if side=='bottom' else int(bary)+10;yb=int(bary)-9 if side=='bottom' else int(bary)+49;patch=sm[yt:yb,xl:xr];rp=res[yt:yb,xl:xr];mask=(patch>=205)&(rp>=20)&(patch==cv2.dilate(patch,np.ones((5,5))));num,labels,stats,centers=cv2.connectedComponentsWithStats(mask.astype('uint8'));peaks=[]
  for i in range(1,num):
   yy,xx=np.where(labels==i);k=int(patch[yy,xx].argmax());x=xl+int(xx[k]);y=yt+int(yy[k]);peaks.append(dict(native_center=[x,y],peak_gray=float(sm[y,x]),local_residual=float(res[y,x]),source_roi=[xl,yt,xr,yb]))
  keep=[]
  for o in sorted(peaks,key=lambda o:-o['peak_gray']):
   if all(abs(o['native_center'][1]-q['native_center'][1])>=11 for q in keep):keep.append(o)
  cap=1+int((bt-t-7)//8);keep=sorted(sorted(keep,key=lambda o:-o['peak_gray'])[:cap],key=lambda o:o['native_center'][1]);entry['columns'].append(dict(side=label,source_roi=[xl,yt,xr,yb],observations=keep));measured.extend((label,lx,o) for o in keep)
 if measured:
  ys=[o['native_center'][1] for _,_,o in measured];phase=min(ys);slots=[round((y-phase)/14.5) for y in ys];mn,mx=min(slots),max(slots);lp=min(12,(bt-t-7)/max(1,mx-mn));origin=(t+bt)/2-(mn+mx)/2*lp
  for (label,lx,o),slot in zip(measured,slots):
   x,y=lx,origin+slot*lp;ev=dict(o,supported=True,algorithm_detected=True,evidence_type='AI_inspected_SD_peak_relative_to_observed_gate_bar',native_gate_bar_anchor=[float(barx),float(bary)]);extra.append(dict(id=f'CTSD2-{gid}-{label}-{slot}',family=f'SD2-{gid}-{label}',column=0,row=int(slot),layer='CT',landing_material='AA',AA_target=aid,layout_center=[x,y],layout_outline=[[x-2.5,y-2.5],[x+2.5,y-2.5],[x+2.5,y+2.5],[x-2.5,y+2.5]],source_frame='poly',source_evidence=ev,status='AI_context_candidate',M1_enclosure='unknown',net_id=None))
 audit.append(entry)
wr(b/'last-SD-body-inspection-v1.json',dict(contacts=extra,regions=audit));wr(b/'all-proposed-final-v1.json',dict(objects=raw+extra));print('added',len(extra),[(x['gate_id'],sum(len(c['observations']) for c in x['columns'])) for x in audit])
