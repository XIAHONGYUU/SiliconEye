"""Resolve duplicate observations and quarantine ownership/geometry conflicts, never repair accepted CT."""
from pathlib import Path
import json,copy,hashlib
from collections import Counter,defaultdict
import cv2,numpy as np
from scipy.signal import find_peaks
from scipy.spatial import cKDTree
from shapely.geometry import Polygon
from shapely.strtree import STRtree
from silicon_eye.ct_joint_reconstruction import audit_contacts
b=Path('benchmarks/ct-full-frame-remaining-v1');p=Path('benchmarks/ct-lower-middle-mos-revision-v2');read=lambda p:json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
mat=read(p/'material-model-v1.json');poly={g['id']:g for g in mat['objects']};parent=read(p/'model-v1.json')['objects'];new=read(b/'all-proposed-frame-refined-v1.json')['objects'];budget=read(p/'spec-v1.json')['budget'];gray=cv2.imread('data/test_chip/tile_full/poly.jpg',0);sm=cv2.GaussianBlur(gray,(5,5),1).astype(float);res=sm-cv2.GaussianBlur(sm,(0,0),4);weak=[]
# AI-inspected end bars: lower-left small MOS tips sit inside obsolete native body extents.
hints={'G65-P05':'bottom','G65-P07':'bottom','G66-P04':'top','G66-P08':'top','SG-U01-001':'bottom','SG-U05-030':'top','SG-U08-067':'bottom'}
for gid,side in hints.items():
 g=poly[gid];pts=np.array(g['native_outline']);nl,nt=pts.min(axis=0);nr,nb=pts.max(axis=0);l,t,r,bt=Polygon(g['layout_outline']).bounds;inset=max(3,int((nr-nl)*.12));xl=int(nl)+inset;xr=int(nr)-inset+1
 yt=int(nt)-6 if side=='top' else int(nt+(nb-nt)*.45);yb=int(nt+(nb-nt)*.55) if side=='top' else int(nb)+7;pa=sm[yt:yb,xl:xr];strength=(np.maximum(pa-180,0)*(res[yt:yb,xl:xr]>=15)).mean(axis=1);sy=yt+int(strength.argmax());xp=sm[max(0,sy-1):sy+2,xl:xr].mean(axis=0);peaks,_=find_peaks(xp,height=190,distance=12);peaks=[int(i) for i in peaks if res[sy,xl+i]>=15];cap=max(1,1+int((r-l-7)//8));peaks=sorted(sorted(peaks,key=lambda i:-xp[i])[:cap]);count=len(peaks);pitch=min(12,(r-l-8)/max(1,count-1));ids=[]
 for j,i in enumerate(peaks):
  x=(l+r)/2+(j-(count-1)/2)*pitch;y=t+4 if side=='top' else bt-4;o=dict(id=f'CTW-{gid}-{j}',family='WEAK-'+gid,column=j,row=0,layer='CT',landing_material='POLY',POLY_target=gid,layout_center=[x,y],layout_outline=[[x-2.5,y-2.5],[x+2.5,y-2.5],[x+2.5,y+2.5],[x-2.5,y+2.5]],source_frame='poly',status='AI_context_guided_weak_terminal_candidate',source_evidence=dict(native_center=[float(xl+i),float(sy)],peak_gray=float(sm[sy,xl+i]),local_residual=float(res[sy,xl+i]),supported=True,evidence_type='AI_inspected_end_bar_bounded_peak_with_plateau_support',algorithm_detected=True,source_roi=[xl,yt,xr,yb],side_hint=side,photographic_native_extent_is_prior_not_exact=True),M1_enclosure='unknown',net_id=None);new.append(o);ids.append(o['id'])
 weak.append(dict(gate_id=gid,side=side,source_roi=[xl,yt,xr,yb],contacts=ids,status='bounded_observed_bar_candidates' if ids else 'no_reliable_peak_even_after_context_inspection'))
write(b/'context-weak-terminals-v1.json',dict(gates=weak))
# Paired small-MOS rows were independently inspected in broad photo context.
# Dense guard rows/internal SD peaks at the opposite end are not gate contacts.
terminal_sides={'G61':'bottom','G62':'top','G65':'bottom','G66':'top'}
retired_direction=[];retained_new=[]
for o in new:
 gid=o.get('POLY_target','');group=gid.split('-')[0]
 if group in terminal_sides and (('-top-' in o['id'] and terminal_sides[group]!='top') or ('-bottom-' in o['id'] and terminal_sides[group]!='bottom')):
  retired_direction.append(dict(candidate=o,reason='AI full-row photo context: opposite end is guard/internal diffusion, not independently established gate terminal',terminal_side=terminal_sides[group]))
 else:retained_new.append(o)
new=retained_new
write(b/'AI-terminal-direction-review-v1.json',dict(group_sides=terminal_sides,source='AI inspection of raw full-row bars and repeated devices, not inheritance of Q2 direction',retired_unaccepted_candidates=retired_direction,parent7044_not_changed=True))
# Quarantine every unresolved competing assignment; safe geometry subset is not full-frame PASS.
held={};duplicates=[]
def hold(o,reason,other=None):
 held.setdefault(o['id'],dict(candidate=o,reasons=[],conflicting_ids=[]));held[o['id']]['reasons'].append(reason)
 if other:held[o['id']]['conflicting_ids'].append(other['id'])
allobs=parent+new;n0=len(parent);points=np.array([o['source_evidence']['native_center'] for o in allobs]);st=cKDTree(points)
for i,j in sorted(st.query_pairs(3.0)):
 if i<n0 and j<n0:continue
 a,z=allobs[i],allobs[j];aid=a.get('POLY_target',a.get('AA_target'));zid=z.get('POLY_target',z.get('AA_target'));dc=float(np.linalg.norm(np.array(a['layout_center'])-z['layout_center']))
 if aid==zid and dc<=8:
  # Repeated peak observations of one cut are retained as provenance, not exported twice.
  keep=i if i<n0 or a['source_evidence'].get('peak_gray',0)>=z['source_evidence'].get('peak_gray',0) else j;lose=j if keep==i else i
  if lose>=n0:hold(allobs[lose],'duplicate_source_and_same_material_local_cut',allobs[keep]);duplicates.append(dict(observation=allobs[lose]['id'],retained=allobs[keep]['id']))
 else:
  reviewed_poly={'G07-P02','G62-P04','SG-U04-080'}
  if a.get('POLY_target') in reviewed_poly and z.get('landing_material')=='AA' and j>=n0:
   hold(z,'AA_locator_lands_on_AI_inspected_gate_tip_not_guard',a)
  elif z.get('POLY_target') in reviewed_poly and a.get('landing_material')=='AA' and i>=n0:
   hold(a,'AA_locator_lands_on_AI_inspected_gate_tip_not_guard',z)
  else:
   if i>=n0:hold(a,'source_ownership_conflict_do_not_use_one_peak_for_distinct_landings',z)
   if j>=n0:hold(z,'source_ownership_conflict_do_not_use_one_peak_for_distinct_landings',a)
# Q3-bottom row1325 is already used by the G18 records; physical ownership needs adjudication.
for o in new:
 if str(o.get('POLY_target','')).startswith('CL2-Q3-AA') and o['source_evidence']['native_center'][1]>=1319:
  hold(o,'source_assignment_conflicts_with_existing_G18_records_requires_landmark')
# A material-correspondence failure invalidates the whole affected NEW source-path recipe,
# not just its inconvenient individual point. Keep all observations in the HOLD queue.
bad_families={x['candidate']['family'] for x in held.values() if x['candidate']['family'].startswith('BAND-') and any('ownership' in r or 'locator' in r for r in x['reasons'])}
for o in new:
 if o['family'] in bad_families:hold(o,'entire_unvalidated_source_path_deferred_after_ownership_counterexample')
write(b/'deferred-source-paths-v1.json',dict(families=sorted(bad_families),why='A locator with an independently observed ownership counterexample cannot be exported as a valid remaining segment',AI_inspected_gate_tips=['G07-P02','G62-P04','SG-U04-080']))
# Q1 native-to-material correspondence is not established: dependent NEW diffusion CT is held too.
for o in new:
 if o.get('AA_target') in {'AA-F01613','AA-F01614'}:
  hold(o,'Q1_material_source_correspondence_pending_do_not_export_dependent_SD')
# Check all geometric conflicts against the complete proposal before selecting an exportable subset.
report=audit_contacts(allobs,mat,budget);byid={o['id']:o for o in new};fullby={o['id']:o for o in allobs}
for key in ['positive_area_overlap_pairs','min_gap_violations']:
 for i,j in report[key]:
  if i in byid:hold(byid[i],key,fullby[j])
  if j in byid:hold(byid[j],key,fullby[i])
for err in report['errors']:
 if err.get('id') in byid:hold(byid[err['id']],err['reason'])
selected=[o for o in new if o['id'] not in held];safe=audit_contacts(parent+selected,mat,budget);assert safe['status']=='PASS',str(safe['errors'][:5])+str(safe['min_gap_violations'][:5])
write(b/'selected-contacts-v1.json',dict(objects=selected));write(b/'quarantined-observations-v1.json',dict(status='HOLD_source_ownership_or_geometry_not_silently_deleted',objects=list(held.values()),duplicate_observation_links=duplicates,all_original_candidates_retained=True,holding_is_not_evidence_of_CT_absence=True));write(b/'whole-proposal-diagnostic-v1.json',report);write(b/'safe-subset-report-v1.json',safe)
# Reconcile every original unreferenced object with its actual final disposition.
priorp={o.get('POLY_target') for o in parent};pc=Counter(o.get('POLY_target') for o in selected);orig=read(b/'gate-inventory-v1.json')['gates'];inventory=[]
for x in orig:
 gid=x['gate_id'];inventory.append(dict(x,exported_contact_count=pc[gid],final_status='source_supported_CT_candidate_exported' if pc[gid] else 'existing_fragment_terminal_retained_elsewhere' if gid.startswith('V3_') else 'unresolved_terminal_ownership_or_observation',quarantined_contact_ids=[k for k,v in held.items() if v['candidate'].get('POLY_target')==gid]))
write(b/'final-material-coverage-v1.json',dict(objects=inventory,already_directly_referenced_materials=len(priorp-{None}),inspected_remaining_materials=len(inventory),newly_referenced_materials=sum(x['exported_contact_count']>0 for x in inventory),unresolved_ids=[x['gate_id'] for x in inventory if x['final_status']=='unresolved_terminal_ownership_or_observation'],not_device_counts=True,full_frame_physical_completion=False))
print(json.dumps(dict(new=len(selected),total=len(parent)+len(selected),held=len(held),held_reason_counts=Counter(r for x in held.values() for r in x['reasons']),newly_referenced=sum(x['exported_contact_count']>0 for x in inventory),unresolved=[x['gate_id'] for x in inventory if x['final_status']=='unresolved_terminal_ownership_or_observation'],weak=weak,safe_geometry=safe['status'])))
