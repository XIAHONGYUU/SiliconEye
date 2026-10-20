"""Correct NEW G49/W05 source phase from independently observed inner/outer photo rows."""
from pathlib import Path
import json,copy
import cv2,numpy as np
from scipy.signal import find_peaks
from shapely.geometry import Polygon
from silicon_eye.ct_transfer import profile_observations,fit_observed_row
from silicon_eye.geometry_reconstruction import object_polygon
b=Path('benchmarks/ct-full-frame-remaining-v1');p=Path('benchmarks/ct-lower-middle-mos-revision-v2');rd=lambda p:json.loads(Path(p).read_text())
def wr(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
mat=rd(p/'material-model-v1.json');gates=sorted([g for g in mat['objects'] if g.get('group_id')=='G49'],key=lambda g:g['id']);aa={a['id']:a for a in mat['AA_objects']};raw=rd(b/'all-proposed-contacts-v1.json')['objects'];retired=[o for o in raw if str(o.get('POLY_target','')).startswith('G49-') or o.get('AA_target') in ['AA-W05','AA-W06']];base=[o for o in raw if o not in retired];gray=cv2.imread('data/test_chip/tile_full/poly.jpg',0);sm=cv2.GaussianBlur(gray,(5,5),1).astype(float);res=sm-cv2.GaussianBlur(sm,(0,0),4);budget=rd(p/'spec-v1.json')['budget'];new=[];measurements=[]
def yline(x,yl,yr):return float(yl+(x-3300)*(yr-yl)/(4660-3300))
def profile(key,material,target,path,axis,layout_start,layout_span,min_gray=190):
 path=np.array(path,float);l,t=np.floor(path.min(axis=0)-4).astype(int);r,bt=np.ceil(path.max(axis=0)+4).astype(int);rc=dict(id=key,axis=axis,material=material,target=target,source_path=path.tolist(),source_roi=[int(l),int(t),int(r),int(bt)],source_origin=0,source_pitch=14.5,source_fit_tolerance=4.5,track_local_spacing=True,layout_origin=list(layout_start),layout_pitch=12,min_gray=min_gray,min_residual=18,sigma=.65,band_half_width=2);rawob=profile_observations(gray,rc);picked=[]
 for o in sorted(rawob['objects'],key=lambda o:-o['source_observation']['peak_gray']):
  if all(abs(o['source_observation']['source_native_center_xy'][axis]-q['source_observation']['source_native_center_xy'][axis])>=11 for q in picked):picked.append(o)
 picked.sort(key=lambda o:o['source_observation']['source_native_center_xy'][axis]);ob=dict(objects=picked)
 if not picked:measurements.append(dict(recipe=rc,raw=rawob,status='no_peak'));return
 rc['source_origin']=picked[0]['source_observation']['source_native_center_xy'][axis];scale=layout_span/(path[-1,axis]-path[0,axis]);rc['layout_pitch']=14.5*scale;rc['layout_origin'][axis]+=(rc['source_origin']-path[0,axis])*scale
 additions,fit=fit_observed_row(ob,rc,budget)
 for o in additions:o['id']='CT49-'+o['id'];o['source_evidence'].update(algorithm_detected=True,source_path=path.tolist(),evidence_type='observed_inner_outer_frame_source_phase_corrected_raw_profile')
 new.extend(additions);measurements.append(dict(recipe=rc,raw=rawob,selected_observation_ids=[o['id'] for o in picked],fit=fit))
a=object_polygon(aa['AA-W06']);l,t,r,bt=a.bounds;gb=[Polygon(g['layout_outline']).bounds for g in gates];lxs=[(l+gb[0][0])/2]+[(a[2]+z[0])/2 for a,z in zip(gb[:-1],gb[1:])]+[(gb[-1][2]+r)/2];native_xs=np.linspace(3255,4706,13)
for i,(x,lx) in enumerate(zip(native_xs,lxs)):
 sy=yline(x,3340,3312);ey=yline(x,3632,3597);profile(f'R49-SD{i:02}','AA','AA-W06',[[x,sy],[x+5,ey]],1,[lx,t+4],bt-t-8)
for i,g in enumerate(gates):
 l,t,r,bt=Polygon(g['layout_outline']).bounds
 for side,lefty,righty,ly in [('bottom',3646,3611,bt-4)]:
  xl=int(native_xs[i]+10);xr=int(native_xs[i+1]-10);hint=yline((xl+xr)/2,lefty,righty);yt=int(hint)-6;yb=int(hint)+7;score=(np.maximum(sm[yt:yb,xl:xr]-195,0)*(res[yt:yb,xl:xr]>=18)).mean(axis=1);sy=yt+int(score.argmax());xp=sm[sy-1:sy+2,xl:xr].mean(axis=0);inds,_=find_peaks(xp,height=205,distance=11);inds=[int(k) for k in inds if res[sy,xl+k]>=18];capacity=1+int((r-l-7)//8);inds=sorted(sorted(inds,key=lambda k:-xp[k])[:capacity]);n=len(inds);lp=min(12,(r-l-8)/max(1,n-1));family=f'R49-G{i+1:02}-{side}'
  for j,k in enumerate(inds):
   x=(l+r)/2+(j-(n-1)/2)*lp;y=ly;new.append(dict(id=f'CT49-{family}-{j:02}',family=family,column=j,row=0,layer='CT',landing_material='POLY',POLY_target=g['id'],layout_center=[x,y],layout_outline=[[x-2.5,y-2.5],[x+2.5,y-2.5],[x+2.5,y+2.5],[x-2.5,y+2.5]],source_frame='poly',source_evidence=dict(native_center=[float(xl+k),float(sy)],peak_gray=float(sm[sy,xl+k]),local_residual=float(res[sy,xl+k]),source_roi=[xl,yt,xr,yb],supported=True,algorithm_detected=True,evidence_type='inner_terminal_row_measured_between_actual_SD_column_anchors',independent_frame_rows='top_outer3297..3271_vs_inner3322..3294; bottom_inner3646..3611_vs_outer3666..3630'),status='AI_source_correspondence_corrected_candidate',M1_enclosure='unknown',net_id=None))
  measurements.append(dict(gate_id=g['id'],side=side,source_roi=[xl,yt,xr,yb],actual_SD_x_limits=[float(native_xs[i]),float(native_xs[i+1])],native_bar_hint=hint,retained_native_centers=[[float(xl+k),float(sy)] for k in inds]))
# Orthogonal ring centres, independently traced around the outer rather than inner source row.
for key,path,axis,origin,span in [('T',[[3238,yline(3238,3322,3294)],[4721,yline(4721,3322,3294)]],0,[3290,3474],1478),('B',[[3245,yline(3245,3666,3630)],[4725,yline(4725,3666,3630)]],0,[3290,3810],1478),('L',[[3230,3310],[3238,3653]],1,[3286,3490],304),('R',[[4728,3283],[4735,3617]],1,[4779,3490],304)]:profile('R49-RING-'+key,'AA','AA-W05',path,axis,origin,span,200)
wr(b/'source-correspondence-repair-v1.json',dict(reason='new source bounding boxes confused G49 top guard row with gate CT; parent RING-BOTTOM source3297..3271 identifies upper resistor guard, next row3322..3294 is G49 upper AA guard. Only bottom3646..3611 is independently observed as gate terminal. Thirteen actualSD columns restore body phase',landmarks=dict(SD_xs=native_xs.tolist(),top_outer_y_at_x3300_4660=[3297,3271],top_inner_gate_y=[3322,3294],bottom_inner_gate_y=[3646,3611],bottom_outer_y=[3666,3630]),retired_unaccepted_candidates=retired,replacement_contacts=new,measurements=measurements,old7044_and_all_material_records_unchanged=True))
wr(b/'all-proposed-repaired-v1.json',dict(objects=base+new));print('retired',len(retired),'replaced',len(new),'all',len(base)+len(new))
