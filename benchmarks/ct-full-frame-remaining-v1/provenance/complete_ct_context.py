"""Inspect remaining AA bands and special terminals; bounded source hypotheses stay auditable."""
from pathlib import Path
import json,copy,hashlib
from collections import Counter,defaultdict
import cv2,numpy as np
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import cKDTree
from shapely.geometry import Polygon,box,LineString,Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
from silicon_eye.ct_transfer import profile_observations,fit_observed_row
from silicon_eye.geometry_reconstruction import object_polygon
root=Path.cwd();b=Path('benchmarks/ct-full-frame-remaining-v1');p=Path('benchmarks/ct-lower-middle-mos-revision-v2');read=lambda p:json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
mat=read(p/'material-model-v1.json');parent=read(p/'model-v1.json')['objects'];base=read(b/'proposed-contacts-v1.json')['objects'];poly={o['id']:o for o in mat['objects']};aa={o['id']:o for o in mat['AA_objects']};allp=unary_union([Polygon(g['layout_outline']) for g in poly.values()]);alla=unary_union([object_polygon(a) for a in aa.values()]);budget=read(p/'spec-v1.json')['budget'];gray=cv2.imread('data/test_chip/tile_full/poly.jpg',0);sm=cv2.GaussianBlur(gray,(5,5),1).astype(float);res=sm-cv2.GaussianBlur(sm,(0,0),4)
new=copy.deepcopy(base);unknown=[];special=[];band_audit=[];bands=[];evidence=[];issues=[]
# Piecewise locator uses photographed POLY centres and old optical measurements, not raw AA-photo coordinates.
anchors=[]
for g in poly.values():
 if not g.get('native_outline'):continue
 ps=np.array(g['native_outline']);q=np.array(g['layout_outline']);anchors.append((q.mean(axis=0).tolist(),ps.mean(axis=0).tolist(),'POLY_centroid_locator_not_CT_confirmation'))
for o in parent:
 e=o['source_evidence']
 if e.get('algorithm_detected') is False or 'estimated' in e.get('native_locator_status',''):continue
 anchors.append((o['layout_center'],e['native_center'],'parent_optical_contact_correspondence'))
loc={}
for layout,native,source in anchors:loc[tuple(map(float,layout))]=native
x=np.array(list(loc));y=np.array(list(loc.values()));interp=LinearNDInterpolator(x,y);tree=cKDTree(x)
def native_points(points):
 points=np.asarray(points,float);result=interp(points);valid=np.isfinite(result).all(axis=1)
 for i in np.flatnonzero(~valid):
  ds,ix=tree.query(points[i],k=12);A=np.c_[x[ix],np.ones(len(ix))];coef=np.linalg.lstsq(A,y[ix],rcond=None)[0];result[i]=np.r_[points[i],1]@coef
 return result,valid

def add(o):
 pcut=Polygon(o['layout_outline']);target=Polygon(poly[o['POLY_target']]['layout_outline']) if o['landing_material']=='POLY' else object_polygon(aa[o['AA_target']]);other=alla if o['landing_material']=='POLY' else allp
 if not target.buffer(-1).covers(pcut) or pcut.distance(other)<1-1e-7:
  issues.append(dict(status='material_landing_conflict_not_exported',candidate=o));return False
 new.append(o);return True

def make_ct(family,slot,xy,native,target,kind,ev):
 xx,yy=map(float,xy);return dict(id=f'CTX-{family}-{slot:03}',family=family,column=int(slot) if kind=='POLY' else 0,row=0 if kind=='POLY' else int(slot),layer='CT',landing_material=kind,layout_center=[xx,yy],layout_outline=[[xx-2.5,yy-2.5],[xx+2.5,yy-2.5],[xx+2.5,yy+2.5],[xx-2.5,yy+2.5]],source_evidence=dict(ev,native_center=list(map(float,native)),supported=True,evidence_type='raw_peak_with_AI_local_material_correspondence',algorithm_detected=True),source_frame='poly',status='AI_context_checked_candidate',M1_enclosure='unknown',net_id=None,**{('POLY_target' if kind=='POLY' else 'AA_target'):target})

# U10 terminal landing: actual source tip is inspected; do not bridge the two fingers.
for gid in ['G68-P01','G68-P02']:
 g=poly[gid];ps=np.array(g['native_outline']);nl,nt=ps.min(axis=0);nr,nb=ps.max(axis=0);gl,gt,gr,gb=Polygon(g['layout_outline']).bounds
 # End pad is the last10 source pixels, not the entire long body.
 xl=int(nl)-3;xr=int(nr)+4;yt=int(nb)-15;yb=int(nb)+6;patch=sm[yt:yb,xl:xr];strength=(np.maximum(patch-195,0)*(res[yt:yb,xl:xr]>=18)).mean(axis=1);sy=yt+int(strength.argmax());xp=sm[sy,xl:xr];peaks=[i for i in range(2,len(xp)-2) if xp[i]>=205 and res[sy,xl+i]>=18 and xp[i]>max(xp[i-2:i].max(),xp[i+1:i+3].max())];chosen=[]
 for i in sorted(peaks,key=lambda i:-xp[i]):
  if all(abs(i-j)>=10 for j in chosen):chosen.append(i)
 # The approved21px pad can carry at most two5px cuts at10px pitch.
 chosen=sorted(chosen[:2]);n=len(chosen);origin=(gl+gr)/2-(n-1)*5;ids=[]
 for j,i in enumerate(chosen):
  ev=dict(peak_gray=float(sm[sy,xl+i]),local_residual=float(res[sy,xl+i]),source_roi=[xl,yt,xr,yb],interpretation='U10 bottom tip optical peak; separate POLY identities retained');ct=make_ct('SPECIAL-'+gid,j,[origin+10*j,gb-4],[xl+i,sy],gid,'POLY',ev)
  if add(ct):ids.append(ct['id'])
 special.append(dict(id=gid,status='source_supported_tip_candidate' if ids else 'unresolved_terminal_peak',source_roi=[xl,yt,xr,yb],contact_ids=ids))
# Previously reviewed V3 body fragments do not include full terminal landing geometry.
for gid in ['V3_G1','V3_G2']:
 special.append(dict(id=gid,status='known_gate_CT_and_M1_ownership_retained_in_historical_network_terminal_outside_current_POLY_body_fragment',action='do_not_shrink_cut_or_bridge_fragments_to_manufacture_full_material_enclosure',historical_refs=['benchmarks/terminal-highlights','benchmarks/network-trace'],new_CT=0,needs_human='only_if_complete_fragment_to_terminal_geometry_is_required'))
# Resistor W01 is horizontal: inspect its left/right contact ends, not top/bottom like a MOS.
gid='SG-U04-W01';g=poly[gid];ps=np.array(g['native_outline']);nl,nt=ps.min(axis=0);nr,nb=ps.max(axis=0);gl,gt,gr,gb=Polygon(g['layout_outline']).bounds
for side,nx,lx in [('left',nl,gl+4),('right',nr,gr-4)]:
 xl=max(0,int(nx)-14);xr=min(gray.shape[1],int(nx)+15);yt=max(0,int(nt)+2);yb=min(gray.shape[0],int(nb)-1);a=sm[yt:yb,xl:xr];strength=(np.maximum(a-190,0)*(res[yt:yb,xl:xr]>=18)).mean(axis=0);sx=xl+int(strength.argmax());yp=sm[yt:yb,sx];peaks=[i for i in range(2,len(yp)-2) if yp[i]>=200 and res[yt+i,sx]>=18 and yp[i]>max(yp[i-2:i].max(),yp[i+1:i+3].max())];chosen=[]
 for i in sorted(peaks,key=lambda i:-yp[i]):
  if all(abs(i-j)>=10 for j in chosen):chosen.append(i)
 cap=max(1,1+int((gb-gt-7)//8));chosen=sorted(chosen[:cap]);n=len(chosen);lp=min(12,(gb-gt-8)/max(1,n-1));ids=[]
 for j,i in enumerate(chosen):
  # axis-aligned vertical contact column, use row index rather than POLY default horizontal family.
  ct=make_ct('RES-W01-'+side,j,[lx,(gt+gb)/2+(j-(n-1)/2)*lp],[sx,yt+i],gid,'POLY',dict(peak_gray=float(sm[yt+i,sx]),local_residual=float(res[yt+i,sx]),source_roi=[xl,yt,xr,yb]));ct['column']=0;ct['row']=j
  if add(ct):ids.append(ct['id'])
 special.append(dict(id=gid,side=side,status='source_supported_resistor_end_candidate' if ids else 'unresolved_resistor_end',source_roi=[xl,yt,xr,yb],contact_ids=ids))
# Decompose guard/other non-MOS AA into orthogonal thin strips. Dummies and crop boundaries have separate dispositions.
gateAA={g.get('AA_target') for g in poly.values()};priorAA={o.get('AA_target') for o in parent};existing_shapes=[Polygon(o['layout_outline']) for o in parent+new];oldtree=STRtree(existing_shapes);existing=parent+new
for aaid,a in aa.items():
 if aaid in gateAA:continue
 if aaid in priorAA:
  band_audit.append(dict(AA_id=aaid,status='prior_scoped_guard_CT_preserved_not_reextracted'));continue
 ap=object_polygon(a);l,t,r,bt=ap.bounds
 dummy=aaid.startswith('D01-') or (aaid.startswith('AA-G') and not ap.interiors) or 'DUMMY' in aaid or (aaid in ['AA-F00052','AA-F00119'])
 if dummy:band_audit.append(dict(AA_id=aaid,status='dummy_geometry_no_CT_inferred_from_bright_edges',source_check='full_frame_context_regular_square_dummy_arrays'));continue
 if l>=5712:band_audit.append(dict(AA_id=aaid,status='outside_reconstructed_main_chip_photo_scope_neighbour_edge_not_extended'));continue
 xs=sorted(set(x for ring in [ap.exterior,*ap.interiors] for x,y in ring.coords));ys=sorted(set(y for ring in [ap.exterior,*ap.interiors] for x,y in ring.coords));parts=[]
 for axis,edges in [(0,ys),(1,xs)]:
  for low,high in zip(edges[:-1],edges[1:]):
   thick=high-low
   if not (7<=thick<=40):continue
   cross=(low+high)/2;line=LineString([(l-1,cross),(r+1,cross)]) if axis==0 else LineString([(cross,t-1),(cross,bt+1)]);hit=ap.intersection(line);segs=list(hit.geoms) if hasattr(hit,'geoms') else [hit]
   for seg in segs:
    if seg.geom_type!='LineString' or seg.length<max(24,3*thick):continue
    pts=np.array(seg.coords);start,end=pts.min(axis=0),pts.max(axis=0);start[axis]+=4;end[axis]-=4;parts.append((axis,start,end,thick))
 if not parts:band_audit.append(dict(AA_id=aaid,status='compact_or_irregular_unassigned_AA_not_automatically_assumed_guard',source_check='inspection_needed_if_terminal_assignment_depends_on_this_island'));continue
 entry=dict(AA_id=aaid,status='all_thin_strips_inspected',strips=[])
 for seq,(axis,start,end,thick) in enumerate(parts):
  name=f'BAND-{aaid}-{seq:02}';sample=np.linspace(start,end,max(3,int((end[axis]-start[axis])/50)+1));mapped,inside=native_points(sample)
  original_scope=[start.tolist(),end.tolist()];valid=(mapped[:,0]>=8)&(mapped[:,1]>=8)&(mapped[:,0]<gray.shape[1]-8)&(mapped[:,1]<gray.shape[0]-8);indices=np.flatnonzero(valid).tolist();keep=[]
  for index in indices:
   if not keep or mapped[index,axis]>mapped[keep[-1],axis]+2:keep.append(index)
  if len(keep)<2:
   entry['strips'].append(dict(id=name,status='outside_photo_or_no_monotonic_visible_locator',layout_path=original_scope,locator_path=mapped.tolist()));continue
  clipped=len(keep)!=len(mapped);sample=sample[keep];mapped=mapped[keep];inside=inside[keep];start=sample[0].copy();end=sample[-1].copy()
  # Refine only within +/-5 pixels; if locator needs a different parallel band it remains a review issue.
  refined=[]
  for q in mapped:
   av=int(round(q[axis]));cr=int(round(q[1-axis]));values=[]
   for off in range(-5,6):
    if axis==0:v=sm[cr+off,av-7:av+8];rr=res[cr+off,av-7:av+8]
    else:v=sm[av-7:av+8,cr+off];rr=res[av-7:av+8,cr+off]
    values.append(float((np.maximum(v-175,0)*(rr>=12)).mean()))
   k=int(np.argmax(values));cross=cr+k-5;refined.append([av,cross] if axis==0 else [cross,av])
  refined=np.array(refined,float);# smooth ridge cross coordinate, preserve monotone along-photo coordinate
  coef=np.polyfit(refined[:,axis],refined[:,1-axis],1);refined[:,1-axis]=np.polyval(coef,refined[:,axis]);lo=np.floor(refined.min(axis=0)-4).astype(int);hi=np.ceil(refined.max(axis=0)+4).astype(int)
  rc=dict(id=name,axis=axis,material='AA',target=aaid,source_path=refined.tolist(),source_roi=[*lo.tolist(),*hi.tolist()],source_origin=0,source_pitch=14.5,source_fit_tolerance=4.5,track_local_spacing=True,layout_origin=start.tolist(),layout_pitch=12,min_gray=205,min_residual=20,sigma=.65,band_half_width=2)
  raw_ob=profile_observations(gray,rc);chosen_ob=[]
  for candidate in sorted(raw_ob['objects'],key=lambda o:-o['source_observation']['peak_gray']):
   if all(abs(candidate['source_observation']['source_native_center_xy'][axis]-q['source_observation']['source_native_center_xy'][axis])>=11 for q in chosen_ob):chosen_ob.append(candidate)
  ob=dict(objects=sorted(chosen_ob,key=lambda o:o['source_observation']['source_native_center_xy'][axis]));detail=dict(id=name,axis=axis,layout_path=[start.tolist(),end.tolist()],locator_path=mapped.tolist(),refined_source_path=refined.tolist(),inside_anchor_hull=inside.tolist(),source_observation_count=len(ob['objects']),raw_observation_count=len(raw_ob['objects']),visible_scope_clipped=clipped,original_layout_scope=original_scope)
  if not ob['objects']:detail['status']='no_retained_profile_peak_not_absence';entry['strips'].append(detail);continue
  rc['source_origin']=ob['objects'][0]['source_observation']['source_native_center_xy'][axis];scale=(end[axis]-start[axis])/(refined[-1,axis]-refined[0,axis]);rc['layout_pitch']=14.5*scale
  if rc['layout_pitch']<8:detail['status']='photo_to_layout_pitch_below_budget';entry['strips'].append(detail);continue
  rc['layout_origin'][axis]+=float((rc['source_origin']-refined[0,axis])*scale)
  try:added,fit=fit_observed_row(ob,rc,budget)
  except ValueError as e:detail.update(status='source_phase_conflict',reason=str(e));entry['strips'].append(detail);continue
  addedids=[];duplicates=[];conflicts=[]
  for ct in added:
   ct['id']='CTX-'+ct['id'];cut=Polygon(ct['layout_outline']);ct['source_evidence'].update(evidence_type='raw_profile_peak_with_piecewise_locator_and_bounded_ridge',algorithm_detected=True,locator_status='AI_photo_correspondence_candidate_not_validated_global_registration',source_path=refined.tolist())
   close=oldtree.query(cut.buffer(3));same=[];bad=[]
   for index in close:
    other=existing[index]
    if cut.distance(existing_shapes[index])>=3-1e-7:continue
    native_distance=float(np.linalg.norm(np.array(ct['source_evidence']['native_center'])-other['source_evidence']['native_center']))
    if other.get('AA_target')==aaid and native_distance<10:same.append(other['id'])
    else:bad.append(other['id'])
   if same and not bad:duplicates.append(dict(candidate=ct['id'],existing_ids=same,reason='same_material_local_source_and_layout_support_already_retained'));continue
   if bad:conflicts.append(dict(candidate=ct,conflicting_ids=bad));continue
   if add(ct):addedids.append(ct['id'])
  detail.update(status='measured_candidates_with_explicit_conflicts' if conflicts else 'measured_candidates_or_existing_support',contact_ids=addedids,existing_support=duplicates,unresolved_conflicts=conflicts,fit=fit);entry['strips'].append(detail);evidence.append(dict(recipe=rc,observations=ob,raw_observations=raw_ob))
 band_audit.append(entry)
write(b/'context-contacts-v1.json',dict(objects=new[len(base):]));write(b/'all-proposed-contacts-v1.json',dict(objects=new));write(b/'special-terminals-v1.json',dict(objects=special));write(b/'AA-band-audit-v1.json',dict(AA_objects=band_audit));write(b/'AA-band-observations-v1.json',dict(measurements=evidence));write(b/'context-issues-v1.json',dict(issues=issues));write(b/'locator-anchors-v1.json',dict(anchors=anchors,method='piecewise_linear_locator_plus_bounded_ridge_not_precise_registration'))
print(json.dumps(dict(new_context=len(new)-len(base),total_new=len(new),count_by_material=Counter(o['landing_material'] for o in new),special=special,AA_band_objects=len(band_audit),strips=sum(len(a.get('strips',[])) for a in band_audit),band_status=Counter(a['status'] for a in band_audit),issues=len(issues))))
