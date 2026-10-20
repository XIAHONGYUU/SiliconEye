"""Prepare full-frame remaining CT observations from existing source/layout correspondences.
Run in repo with .venv Python; never edits photos or accepted records. Output is candidate evidence.
"""
from pathlib import Path
import json,hashlib,copy
from collections import defaultdict,Counter
import cv2,numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from silicon_eye.ct_transfer import profile_observations,fit_observed_row
from silicon_eye.geometry_reconstruction import object_polygon
root=Path.cwd();base=Path('benchmarks/ct-lower-middle-mos-revision-v2');b=Path('benchmarks/ct-full-frame-remaining-v1');b.mkdir(exist_ok=True)
def read(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
mat=read(base/'material-model-v1.json');parent=read(base/'model-v1.json')['objects'];budget=read(base/'spec-v1.json')['budget'];poly={g['id']:g for g in mat['objects']};aa={a['id']:a for a in mat['AA_objects']};pg={k:Polygon(g['layout_outline']) for k,g in poly.items()};allp=unary_union(list(pg.values()));alla=unary_union([object_polygon(a) for a in aa.values()]);gray=cv2.imread('data/test_chip/tile_full/poly.jpg',0);sm=cv2.GaussianBlur(gray,(5,5),1).astype(float);res=sm-cv2.GaussianBlur(sm,(0,0),4)
priorpoly={o.get('POLY_target') for o in parent};prioraa={o.get('AA_target') for o in parent};missing=[g for g in poly.values() if g['id'] not in priorpoly];new=[];observations=[];issues=[];gate_inventory=[];AA_inventory=[];profile_recipes=[];direct_recipes=[]
def bounds(g,key='layout_outline'):return Polygon(g[key]).bounds

def add_contact(family,slot,xy,native,target,material,evidence,role):
 x,y=map(float,xy);o=dict(id=f'CTR-{family}-{slot:03}',family=family,column=int(slot) if material=='POLY' else 0,row=0 if material=='POLY' else int(slot),layer='CT',landing_material=material,layout_center=[x,y],layout_outline=[[x-2.5,y-2.5],[x+2.5,y-2.5],[x+2.5,y+2.5],[x-2.5,y+2.5]],source_frame='poly',status='AI_full_frame_local_correspondence_candidate',source_evidence=dict(evidence,native_center=[float(native[0]),float(native[1])],supported=True,evidence_type='raw_peak_with_AI_local_material_correspondence',algorithm_detected=True),terminal_role=role,M1_enclosure='unknown',net_id=None)
 o['POLY_target' if material=='POLY' else 'AA_target']=target
 p=Polygon(o['layout_outline']);targetpg=pg[target] if material=='POLY' else object_polygon(aa[target]);other=alla if material=='POLY' else allp
 if not targetpg.buffer(-1).covers(p) or p.distance(other)<1-1e-7:
  issues.append(dict(id=o['id'],target=target,status='material_landing_conflict_not_exported',candidate=o));return None
 new.append(o);return o

# All retained bright points are optical observations, whether or not a material assignment exports.
for g in missing:
 gid=g['id'];ps=np.array(g['native_outline'],float)
 if len(ps)<3:issues.append(dict(id=gid,status='missing_source_polygon'));continue
 nl,nt,nr,nb=bounds(g,'native_outline');gl,gt,gr,gb=bounds(g);horizontal=(nr-nl)>(nb-nt)*3 and (gr-gl)>(gb-gt)*3
 inventory=dict(gate_id=gid,group=g.get('group_id'),kind=g.get('kind'),AA_target=g.get('AA_target'),sides=[],contact_count=0)
 # Horizontal fragments and U10 lack established terminal extents; inspect separately, do not stretch them.
 if horizontal or g.get('kind')=='U10_separate_gate_finger_candidate_not_device_count':
  inventory.update(status='special_terminal_scope_requires_separate_review');gate_inventory.append(inventory);continue
 for side,ny,ly in [('top',nt,gt+4),('bottom',nb,gb-4)]:
  inset=max(3,int((nr-nl)*.12));radius=26 if nb-nt>=90 else 14
  x1=max(0,int(np.ceil(nl+inset)));x2=min(gray.shape[1],int(np.floor(nr-inset))+1);y1=max(0,int(ny)-radius);y2=min(gray.shape[0],int(ny)+radius+1)
  if x2-x1<7:continue
  row_strength=(np.maximum(sm[y1:y2,x1:x2]-195,0)*(res[y1:y2,x1:x2]>=20)).mean(axis=1);iy=int(row_strength.argmax());sy=y1+iy;xp=sm[max(0,sy-1):sy+2,x1:x2].mean(axis=0)
  maxima=[i for i in range(2,len(xp)-2) if row_strength[iy]>=6 and xp[i]>=205 and xp[i]>max(xp[i-2:i].max(),xp[i+1:i+3].max()) and res[sy,x1+i]>=20]
  chosen=[]
  for i in sorted(maxima,key=lambda i:-xp[i]):
   if all(abs(i-j)>=12 for j in chosen):chosen.append(i)
  chosen.sort();capacity=max(1,1+int((gr-gl-7)//8));chosen=sorted(sorted(chosen,key=lambda i:-xp[i])[:capacity]);raw=[]
  for i in chosen:
   x=x1+i;raw.append(dict(native_center=[int(x),int(sy)],peak_gray=float(sm[sy,x]),local_residual=float(res[sy,x]),source_roi=[x1,y1,x2,y2]))
  observations.append(dict(material_id=gid,side=side,source_roi=[x1,y1,x2,y2],observations=raw,interpretation='bounded native endpoint inspection; visible presence not electrical connection'))
  if not raw:inventory['sides'].append(dict(side=side,count=0,status='no_retained_peak_not_absence'));continue
  # Preserve regular geometry independently of camera skew. Count comes from actual retained peaks.
  pitch=min(12,(gr-gl-8)/max(1,len(raw)-1));origin=(gl+gr)/2-(len(raw)-1)*pitch/2;added=[]
  for j,o in enumerate(raw):
   ct=add_contact('G-'+gid+'-'+side,j,[origin+j*pitch,ly],o['native_center'],gid,'POLY',o,'gate_or_POLY_terminal_candidate')
   if ct:added.append(ct['id'])
  inventory['sides'].append(dict(side=side,count=len(added),contact_ids=added,status='measured_source_candidate' if added else 'observed_but_canonical_landing_conflict'))
  inventory['contact_count']+=len(added)
 inventory['status']='measured_terminal_candidate' if inventory['contact_count'] else 'no_exportable_terminal_observation';gate_inventory.append(inventory)

# Native-to-canonical mapping is local to each AA family, using explicit POLY edges.
byAA=defaultdict(list)
for g in poly.values():
 if g.get('AA_target') in aa:byAA[g['AA_target']].append(g)
def interp_extra(x,xs,ys):
 if len(xs)==1:return float(ys[0])
 if x<xs[0]:return float(ys[0]+(x-xs[0])*(ys[1]-ys[0])/(xs[1]-xs[0]))
 if x>xs[-1]:return float(ys[-1]+(x-xs[-1])*(ys[-1]-ys[-2])/(xs[-1]-xs[-2]))
 return float(np.interp(x,xs,ys))
def local_map(gates,x,y):
 pairs=[];ys=[]
 for g in gates:
  l,t,r,bt=bounds(g);ps=np.array(g['native_outline']);nl,nt,nr,nb=bounds(g,'native_outline');v=(y-t)/(bt-t);toppts=ps[abs(ps[:,1]-nt)<1e-3];botpts=ps[abs(ps[:,1]-nb)<1e-3];tx=float(toppts[:,0].mean()) if len(toppts) else (nl+nr)/2;bx=float(botpts[:,0].mean()) if len(botpts) else (nl+nr)/2;nx=tx+(bx-tx)*v;nw=nr-nl-abs(bx-tx);pairs.extend([(l,nx-nw/2),(r,nx+nw/2)]);ys.append(((l+r)/2,nt+v*(nb-nt)))
 # Duplicate x coordinates can occur in partial source fragments; their mapping remains unresolved.
 pairs.sort();xx=[];vv=[]
 for k in sorted(set(z[0] for z in pairs)):xx.append(k);vv.append(float(np.median([z[1] for z in pairs if z[0]==k])))
 ys.sort();return [interp_extra(x,xx,vv),interp_extra(x,[z[0] for z in ys],[z[1] for z in ys])]

for aaid,gates in byAA.items():
 if aaid in prioraa:continue
 ap=object_polygon(aa[aaid]);l,t,r,bt=ap.bounds;entry=dict(AA_id=aaid,gate_ids=[g['id'] for g in gates],source_map='piecewise_interpolation_of_native_POLY_edges_within_same_AA',columns=[],status='inspected')
 if any(len(g['native_outline'])<4 for g in gates):entry['status']='incomplete_native_geometry';AA_inventory.append(entry);continue
 free=ap.buffer(-3.5).difference(unary_union([pg[g['id']].buffer(3.5,join_style=2) for g in gates]));parts=list(free.geoms) if hasattr(free,'geoms') else [free];parts=sorted([q for q in parts if q.area>1 and q.bounds[3]-q.bounds[1]>=5],key=lambda p:p.centroid.x)
 # A wide/nested polygon may have horizontal voids that are not a SD column; do not silently force a rectangle.
 prepared=[]
 for i,q in enumerate(parts):
  ql,qt,qr,qb=q.bounds;x=float(q.centroid.x)
  if not q.buffer(1e-6).covers(box(x-.01,qt+.01,x+.01,qb-.01)):continue
  native_top=np.array(local_map(gates,x,t));native_bot=np.array(local_map(gates,x,bt));dy=native_bot[1]-native_top[1]
  if dy<=0:issues.append(dict(id=aaid,status='nonmonotonic_local_source_map'));continue
  # Padding allows boundary peaks to be measured, but eligibility stays inside the native AA hypothesis.
  v=(native_bot-native_top)/dy;start=native_top-v*7;end=native_bot+v*7
  if min(start)<0 or end[0]>=gray.shape[1]-4 or end[1]>=gray.shape[0]-4:entry['columns'].append(dict(column=i,status='source_photo_boundary',source_path=[start.tolist(),end.tolist()]));continue
  path=[start.tolist(),end.tolist()];pts=np.array(path);lo=np.floor(pts.min(axis=0)-4).astype(int);hi=np.ceil(pts.max(axis=0)+4).astype(int)
  recipe=dict(id=f'REM-{aaid}-SD{i:02}',material='AA',target=aaid,axis=1,source_path=path,source_roi=[*lo.tolist(),*hi.tolist()],source_origin=0,source_pitch=14.5,source_fit_tolerance=5.7,track_local_spacing=True,layout_origin=[x,t+4],layout_pitch=12,min_gray=195,min_residual=20,sigma=.65,band_half_width=2)
  measured=profile_observations(gray,recipe);eligible=[o for o in measured['objects'] if native_top[1]-2<=o['source_observation']['source_native_center_xy'][1]<=native_bot[1]+2]
  observations.append(dict(AA_id=aaid,column=i,source_path=path,source_native_AA_y=[float(native_top[1]),float(native_bot[1])],objects=measured['objects'],eligible_observation_ids=[o['id'] for o in eligible]))
  col=dict(column=i,source_path=path,free_column_bbox=[ql,qt,qr,qb],layout_x=x,observed_count=len(eligible))
  if not eligible:col['status']='no_retained_source_peak_not_absence';entry['columns'].append(col);continue
  prepared.append((i,q,x,native_top,native_bot,recipe,eligible,col))
 # Use all observed columns to establish a shared row phase; never derive pitch from observed count.
 if prepared:
  starts=[o['source_observation']['source_native_center_xy'][1]-nt[1] for _,_,_,nt,nb,rc,os,c in prepared for o in os]
  candidates=np.arange(13,16.1,.1);best=None
  for pitch in candidates:
   phases=np.mod(starts,pitch)
   for phase in phases:
    err=np.abs((np.array(starts)-phase+pitch/2)%pitch-pitch/2);score=float(np.median(err))
    if best is None or score<best[0]:best=(score,float(pitch),float(phase))
  _,sp,phase=best
  slots=[]
  for i,q,x,nt,nb,rc,os,col in prepared:
   for o in os:slots.append(round((o['source_observation']['source_native_center_xy'][1]-nt[1]-phase)/sp))
  mn,mx=min(slots),max(slots);scale=float(np.median([(bt-t)/(nb[1]-nt[1]) for _,_,_,nt,nb,_,_,_ in prepared]));lp=sp*scale
  # Keep the measured period. A large required compression signals source/model disagreement.
  capacity_pitch=(bt-t-7)/max(1,mx-mn)
  if mx>mn and lp>capacity_pitch*1.3:
   entry['status']='row_extent_disagrees_with_current_AA';issues.append(dict(id=aaid,status=entry['status'],source_pitch=sp,layout_pitch=lp,available_pitch=capacity_pitch,observed_slot_range=[mn,mx]));AA_inventory.append(entry);continue
  if mx>mn:lp=min(lp,capacity_pitch)
  if mx>mn and lp<8:
   entry['status']='row_pitch_below_original_budget';issues.append(dict(id=aaid,status=entry['status']));AA_inventory.append(entry);continue
  proposed=t+phase*scale;origin=max(t+3.5-mn*lp,min(proposed,bt-3.5-mx*lp));entry.update(source_pitch=sp,layout_pitch=lp,layout_origin_y=origin,observed_slot_range=[mn,mx])
  for i,q,x,nt,nb,rc,os,col in prepared:
   rc.update(source_origin=float(nt[1]+phase),source_pitch=sp,layout_origin=[x,origin],layout_pitch=lp)
   try:added,fit=fit_observed_row(dict(objects=os),rc,budget)
   except ValueError as e:col['status']='source_phase_conflict';col['reason']=str(e);entry['columns'].append(col);continue
   ids=[]
   for o in added:
    o['id']='CTR-'+o['id'];y=o['layout_center'][1];p=Polygon(o['layout_outline']);e=o['source_evidence'];ob=add_contact(rc['id'],o['row'],[x,y],e['native_center'],aaid,'AA',e,'source_drain_diffusion_candidate')
    if ob:ids.append(ob['id'])
   col.update(status='source_supported_candidates' if ids else 'no_exportable_source_observation',contact_ids=ids,fit=fit);entry['columns'].append(col);profile_recipes.append(rc)
 AA_inventory.append(entry)

write(b/'proposed-contacts-v1.json',dict(objects=new));write(b/'observations-v1.json',dict(observations=observations));write(b/'gate-inventory-v1.json',dict(gates=gate_inventory));write(b/'AA-inventory-v1.json',dict(families=AA_inventory));write(b/'issues-v1.json',dict(issues=issues));write(b/'profile-recipes-v1.json',dict(rows=profile_recipes));print(json.dumps(dict(new=len(new),counts=Counter(o['landing_material'] for o in new),inspected_materials=len(gate_inventory),with_new_gateCT=sum(g['contact_count']>0 for g in gate_inventory),AA_families=len(AA_inventory),issues=len(issues),by_gate_status=Counter(g['status'] for g in gate_inventory),AA_status=Counter(a['status'] for a in AA_inventory))))
