"""Reinspect only unobserved/phase-conflicting new SD columns using bounded raw ridges."""
from pathlib import Path
import json,copy
from collections import Counter
import cv2,numpy as np
from scipy.signal import find_peaks
from shapely.geometry import Polygon
from shapely.ops import unary_union
from silicon_eye.ct_transfer import profile_observations,fit_observed_row
from silicon_eye.geometry_reconstruction import object_polygon
b=Path('benchmarks/ct-full-frame-remaining-v1');p=Path('benchmarks/ct-lower-middle-mos-revision-v2');rd=lambda p:json.loads(Path(p).read_text())
def wr(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
mat=rd(p/'material-model-v1.json');aa={a['id']:a for a in mat['AA_objects']};poly={o['id']:o for o in mat['objects']};allp=unary_union([Polygon(o['layout_outline']) for o in poly.values()]);families=rd(b/'AA-inventory-v1.json')['families'];obs=rd(b/'observations-v1.json')['observations'];obmap={(o['AA_id'],o['column']):o for o in obs if 'AA_id' in o};recipes=rd(b/'profile-recipes-v1.json')['rows'];recs={r['id']:r for r in recipes};gray=cv2.imread('data/test_chip/tile_full/poly.jpg',0);sm=cv2.GaussianBlur(gray,(5,5),1).astype(float);res=sm-cv2.GaussianBlur(sm,(0,0),4);budget=rd(p/'spec-v1.json')['budget'];new=[];audit=[]
for family in families:
 aid=family['AA_id'];ap=object_polygon(aa[aid]);l,t,r,bt=ap.bounds
 if aid in ['AA-W06','AA-F01613','AA-F01614']:continue
 for col in family['columns']:
  if col.get('status') not in ['no_retained_source_peak_not_absence','source_phase_conflict']:continue
  i=col['column'];rec=obmap.get((aid,i));
  if rec is None:continue
  path=np.array(rec['source_path']);axis=1;av=np.arange(int(path[0,1])+7,int(path[-1,1])-6,dtype=float)
  if len(av)<5:continue
  cross=np.interp(av,path[:,1],path[:,0]);scores=[]
  # Neighbouring POLY bodies constrain allowed diffusion search. Avoid crossing a gate or the outer guard.
  cx=col['layout_x'];gates=[poly[k] for k in family['gate_ids']];gatebounds=[Polygon(g['layout_outline']).bounds for g in gates];lefts=[j for j,bb in enumerate(gatebounds) if bb[2]<cx];rights=[j for j,bb in enumerate(gatebounds) if bb[0]>cx]
  def source_edge(g,yy,edge):
   q=np.array(g['native_outline']);nl,nt=q.min(axis=0);nr,nb=q.max(axis=0);top=q[abs(q[:,1]-nt)<1e-3,0].mean();bottom=q[abs(q[:,1]-nb)<1e-3,0].mean();mid=top+(bottom-top)*(yy-nt)/(nb-nt);w=nr-nl-abs(bottom-top);return mid+(-w/2 if edge=='left' else w/2)
  sy=float(np.median(av));minx=-np.inf;maxx=np.inf
  if lefts:
   gi=max(lefts,key=lambda j:gatebounds[j][2]);minx=source_edge(gates[gi],sy,'right')+2
  if rights:
   gi=min(rights,key=lambda j:gatebounds[j][0]);maxx=source_edge(gates[gi],sy,'left')-2
  if not lefts and rights:minx=maxx-25
  if not rights and lefts:maxx=minx+25
  for off in range(-16,17):
   if not minx<=float(np.median(cross))+off<=maxx:scores.append(-1);continue
   xs=(cross+off).astype(np.float32)[None,:];ys=av.astype(np.float32)[None,:];v=cv2.remap(sm.astype(np.float32),xs,ys,cv2.INTER_LINEAR)[0];rr=cv2.remap(res.astype(np.float32),xs,ys,cv2.INTER_LINEAR)[0];scores.append(float((np.maximum(v-175,0)*(rr>=14)).mean()))
  off=int(np.argmax(scores))-16;entry=dict(AA_id=aid,column=i,source_path_before=path.tolist(),offset_x=off,allowed_source_x=[float(minx),float(maxx)],ridge_score=max(scores),candidate_ids=[])
  if max(scores)<=0:entry['status']='no_diffusion_ridge_in_bounded_window';audit.append(entry);continue
  path[:,0]+=off;lo=np.floor(path.min(axis=0)-4).astype(int);hi=np.ceil(path.max(axis=0)+4).astype(int);rc=dict(id=f'RECOVER-{aid}-SD{i:02}',axis=1,material='AA',target=aid,source_path=path.tolist(),source_roi=[*lo.tolist(),*hi.tolist()],source_origin=0,source_pitch=14.5,source_fit_tolerance=5.7,track_local_spacing=True,layout_origin=[cx,t+4],layout_pitch=12,min_gray=185,min_residual=16,sigma=.65,band_half_width=2)
  measured=profile_observations(gray,rc);nt,nb=rec['source_native_AA_y'];eligible=[o for o in measured['objects'] if nt-1<=o['source_observation']['source_native_center_xy'][1]<=nb+1]
  # Explicitly support clipped/flat-top photographic peaks rather than fabricating expected counts.
  if not eligible:
   allav=np.arange(int(path[0,1]),int(path[-1,1])+1,dtype=np.float32);cr=np.interp(allav,path[:,1],path[:,0]);xs=np.tile(cr,(5,1)).astype(np.float32)+np.arange(-2,3,dtype=np.float32)[:,None];ys=np.tile(allav,(5,1));band=cv2.remap(gray,xs,ys,cv2.INTER_LINEAR).astype(float);v=cv2.GaussianBlur(band.mean(axis=0)[None,:],(0,0),.65)[0];indices,_=find_peaks(v,height=185,distance=10,prominence=16)
   for j in indices:
    if not nt-1<=allav[j]<=nb+1:continue
    ix=int(band[:,j].argmax());x=float(xs[ix,j]);y=float(ys[ix,j]);eligible.append(dict(id=f'PLATEAU-{aid}-{i}-{j}',evidence_tier='bounded_ridge_plateau_profile_peak',source_observation=dict(source_native_center_xy=[x,y],peak_gray=float(v[j]),local_residual=float(v[j]-min(v[max(0,j-6):j+7])))))
  entry['measured_observations']=eligible
  if not eligible:entry['status']='no_peak_after_ridge_and_plateau_inspection_not_absence';audit.append(entry);continue
  scales=(bt-t)/(nb-nt);sp=family.get('source_pitch',14.5);lp=family.get('layout_pitch',sp*scales);origin=family.get('layout_origin_y',t+3.5)
  previous=next((rr for rr in recipes if rr['target']==aid),None)
  if previous:
   # Derive source phase from a measured sibling, not from a desired count.
   prevcol=int(previous['id'].rsplit('SD',1)[1]);pr=obmap[(aid,prevcol)];phase=previous['source_origin']-pr['source_native_AA_y'][0];rc['source_origin']=nt+phase;rc['source_pitch']=sp
  else:
   rc['source_origin']=eligible[0]['source_observation']['source_native_center_xy'][1];rc['source_pitch']=14.5;origin=t+(rc['source_origin']-nt)*scales
  rc['layout_origin']=[cx,origin];rc['layout_pitch']=lp
  try:additions,fit=fit_observed_row(dict(objects=eligible),rc,budget)
  except ValueError as e:entry.update(status='source_phase_still_conflicts',reason=str(e));audit.append(entry);continue
  for o in additions:
   o['id']='CTSD-'+o['id'];o['source_evidence'].update(evidence_type='bounded_diffusion_ridge_with_AI_material_context',algorithm_detected=True,source_path=path.tolist(),native_ridge_shift_x=off);q=Polygon(o['layout_outline'])
   if not ap.buffer(-1).covers(q) or q.distance(allp)<1-1e-7:
    entry.setdefault('material_conflicts',[]).append(o);continue
   new.append(o);entry['candidate_ids'].append(o['id'])
  entry.update(status='recovered_measured_source_candidates' if entry['candidate_ids'] else 'observed_peaks_but_material_mapping_unresolved',fit=fit,recipe=rc);audit.append(entry)
raw=rd(b/'all-proposed-repaired-v1.json')['objects'];wr(b/'all-proposed-with-SD-recovery-v1.json',dict(objects=raw+new));wr(b/'SD-recovery-v1.json',dict(new_contacts=new,inspected_columns=audit,thresholds=dict(min_gray=185,min_residual=16,max_native_cross_shift=16,source_search_constrained_by_adjacent_POLY=True),not_assumed_absent_on_no_detection=True));print('recovered',len(new),'columns',len(audit),'status',dict(Counter(x['status'] for x in audit)))
