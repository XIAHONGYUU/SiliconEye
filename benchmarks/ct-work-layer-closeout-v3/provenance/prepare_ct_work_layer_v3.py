"""Prepare source-path cleanup and an evidence-only terminal-access inventory.
Run from repo with .venv Python. Audit recipe; production execution uses ct_transfer.
"""
from pathlib import Path
import copy,json,hashlib
from collections import Counter,defaultdict
import cv2,numpy as np
from scipy.signal import find_peaks
from scipy.spatial import cKDTree
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
from silicon_eye.geometry_reconstruction import object_polygon
from silicon_eye.ct_transfer import profile_observations,fit_observed_row,audit_terminal_access,apply_source_correspondence_corrections
from silicon_eye.ct_joint_reconstruction import audit_contacts
B=Path('benchmarks/ct-work-layer-closeout-v3');P=Path('benchmarks/ct-full-frame-adjudication-v2');V1=Path('benchmarks/ct-full-frame-remaining-v1');B.mkdir(exist_ok=True);assert not (B/'model-v1.json').exists()
def rd(p):return json.loads(Path(p).read_text())
def wr(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
mat=rd(P/'material-model-v1.json');parent=rd(P/'model-v1.json')['objects'];byid={o['id']:o for o in parent};poly={o['id']:o for o in mat['objects']};aa={o['id']:o for o in mat['AA_objects']};budget=rd(P/'spec-v1.json')['budget'];gray=cv2.imread('data/test_chip/tile_full/poly.jpg',0);smooth=cv2.GaussianBlur(gray,(5,5),1).astype(float);residual=smooth-cv2.GaussianBlur(smooth,(0,0),4)
# A source counterexample at the U10 guard corner requires checking all four NEW source recipes.
# The already human-reviewed 7044 geometry remains outside this retirement scope.
extra_bad_families={'BAND-AA2-LEFT-GUARD-NETWORK-SHARED-GUARDS-2-00','BAND-AA2-TOP-STEP-1-AA-0-02'}
retired=[o for o in parent if o.get('AA_target')=='AA-G001' or o['family'] in extra_bad_families];assert all(o['id'].startswith('CTX-') for o in retired)
changes=[dict(id=o['id'],before=o,after=None,reason='unaccepted source recipe failed independent frame/row ownership checks; retire the entire affected recipe, not just conflicting points; named reinspection supplies new evidence') for o in retired];working=[o for o in parent if o['id'] not in {x['id'] for x in retired}]
optical=[];corrections=[]
def inspect_peak(tag,bb):
 l,t,r,b=bb;patch=residual[t:b,l:r];dy,dx=np.unravel_index(patch.argmax(),patch.shape);x=l+int(dx);y=t+int(dy);support=bool(smooth[y,x]>=205 and residual[y,x]>=20);ev=dict(native_center=[x,y],source_native_center_xy=[x,y],peak_gray=float(smooth[y,x]),local_residual=float(residual[y,x]),source_roi=bb,supported=support,algorithm_detected=True,evidence_type='bounded_raw_peak_with_AI_material_and_terminal_context',source_observation_id=tag)
 optical.append(dict(id=tag,source_evidence=ev));return ev
# Correct newly inspected neighbouring source points; all design identity/geometry remains fixed.
def correction(key,bb):
 old=byid[key];ev=inspect_peak('V3-RELOCALIZE-'+key,bb);assert ev['supported'],key
 corrections.append(dict(id=key,before_source_evidence=old['source_evidence'],after_source_evidence=ev,reason='independent source-row/column reinspection after the access audit; prior measurement retained in history; design and approved topology unchanged'))
key=next(o['id'] for o in parent if o.get('AA_target')=='AA2-LEFT-GUARD-NETWORK-LOWER-LEFT-CELLS-BRANCH-AA2-0' and o['source_evidence']['native_center'][0]<1100);correction(key,[1105,3368,1125,3382])
key=next(o['id'] for o in parent if o.get('AA_target')=='AA2-LEFT-GUARD-NETWORK-LOWER-LEFT-CELLS-ROW4-AA4-0');correction(key,[1162,3738,1182,3755])
key=next(o['id'] for o in parent if o.get('AA_target')=='AA2-LEFT-GUARD-NETWORK-LOWER-LEFT-CELLS-ROW4-AA8-0');correction(key,[1480,3732,1504,3752])
# The final G66 finger's old 'top' picks were on the body row, not the actual upper terminal bar.
peaks=[];roi=[1498,3707,1533,3724];l,t,r,b=roi;ys=np.maximum(smooth[t:b,l:r]-190,0).mean(axis=1);sy=t+int(ys.argmax());xp=smooth[sy,l:r];ix,_=find_peaks(xp,height=205,distance=9,prominence=7);peaks=[int(l+i) for i in ix if residual[sy,l+i]>=20];assert len(peaks)>=2,peaks
for old,x in zip([o for o in parent if o.get('POLY_target')=='G66-P08'],peaks[:2],strict=True):correction(old['id'],[x-3,sy-2,x+4,sy+3])
review=dict(date='2026-10-21',user_instruction_verbatim='可以，继续推进这三条工作',scope='execution authorization for source cleanup, full-frame joint candidate, and preparation of final overall human review; not blanket physical acceptance',authorized_material_ids=[],authorized_contact_ids=[o['id'] for o in retired],authorized_source_correspondence_ids=[c['id'] for c in corrections],authorized_new_contact_ids=[],preserve_prior_human_decisions=True,whole_frame_human_accepted=False)
wr(B/'authorization-v1.json',review)
working=apply_source_correspondence_corrections(working,corrections,review['authorized_source_correspondence_ids'],ref(B/'authorization-v1.json'))
new=[];candidate_decisions=[];path_reviews=[];unknown=[];profiles=[]
BASESHAPES=[Polygon(o['layout_outline']) for o in working];BASETREE=STRtree(BASESHAPES);SOURCETREE=cKDTree(np.array([o['source_evidence']['native_center'] for o in working]))
# Whole-model checks plus optical ownership: never solve a conflict by lowering the budget.
def try_add(o,context):
 p=Polygon(o['layout_outline']);target=Polygon(poly[o['POLY_target']]['layout_outline']) if o['landing_material']=='POLY' else object_polygon(aa[o['AA_target']]);other=unary_union([object_polygon(a) for a in mat['AA_objects']]) if o['landing_material']=='POLY' else ALLPOLY
 reason=None
 if not o['source_evidence']['supported']:reason='no_observed_source_support'
 elif not target.buffer(-1).covers(p) or p.distance(other)<1-1e-7:reason='material_landing_or_channel_clearance'
 else:
  for q in [working[i] for i in SOURCETREE.query_ball_point(o['source_evidence']['native_center'],3)]+new:
   if np.linalg.norm(np.array(q['source_evidence']['native_center'])-o['source_evidence']['native_center'])<=3:
    reason='source_already_retained_same_target' if q.get('AA_target',q.get('POLY_target'))==o.get('AA_target',o.get('POLY_target')) else 'source_competing_assignment_preserved_unknown';break
  if reason is None:
   if any(p.distance(BASESHAPES[i])<3-1e-7 for i in BASETREE.query(p.buffer(3))) or any(p.distance(Polygon(q['layout_outline']))<3-1e-7 for q in new):reason='whole_model_CT_spacing_conflict'
 candidate_decisions.append(dict(id=o['id'],context=context,decision=reason or 'export_candidate',candidate=o))
 if reason:return False
 new.append(o);return True
ALLPOLY=unary_union([Polygon(g['layout_outline']) for g in mat['objects']])
def ct(key,target,xy,ev,kind='AA',family=None,column=0,row=0):
 x,y=map(float,xy);return dict(id=key,family=family or key,column=column,row=row,layer='CT',landing_material=kind,**{('AA_target' if kind=='AA' else 'POLY_target'):target},layout_center=[x,y],layout_outline=[[x-2.5,y-2.5],[x+2.5,y-2.5],[x+2.5,y+2.5],[x-2.5,y+2.5]],source_frame='poly',source_evidence=ev,status='AI_source_checked_work_layer_candidate',M1_enclosure='unknown',net_id=None)
def profile(key,target,path,layout_path,export=True,side='AA_guard'):
 axis=0 if abs(path[-1][0]-path[0][0])>abs(path[-1][1]-path[0][1]) else 1;path=sorted(path,key=lambda p:p[axis]);layout_path=sorted(layout_path,key=lambda p:p[axis]);pts=np.array(path);lo=np.maximum(0,np.floor(pts.min(axis=0)-5)).astype(int);hi=np.minimum([gray.shape[1]-1,gray.shape[0]-1],np.ceil(pts.max(axis=0)+5)).astype(int)
 row=dict(id=key,axis=axis,material='AA',target=target,source_path=path,source_roi=[*lo.tolist(),*hi.tolist()],source_origin=0,source_pitch=15.3,source_fit_tolerance=4.5,track_local_spacing=True,layout_origin=layout_path[0],layout_pitch=15,band_half_width=2,sigma=.65,min_gray=205,min_residual=20)
 obs=profile_observations(gray,row);observed=[]
 for o in sorted(obs['objects'],key=lambda o:-o['source_observation']['peak_gray']):
  if all(abs(o['source_observation']['source_native_center_xy'][axis]-z['source_observation']['source_native_center_xy'][axis])>=11 for z in observed):observed.append(o)
 observed=sorted(observed,key=lambda o:o['source_observation']['source_native_center_xy'][axis]);ev=dict(id=key,target=target,source_path=path,layout_path=layout_path,role=side,observation_count=len(observed),AI_export_authorized=export,observations=observed)
 profiles.append(ev)
 if not observed or not export:return []
 first=observed[0]['source_observation']['source_native_center_xy'][axis];scale=(layout_path[-1][axis]-layout_path[0][axis])/(path[-1][axis]-path[0][axis]);row['source_origin']=first;row['layout_origin']=list(layout_path[0]);row['layout_origin'][axis]+=(first-path[0][axis])*scale;row['layout_pitch']=15.3*scale
 if row['layout_pitch']<8:ev['export_failure']='source_to_design_pitch_cannot_satisfy_budget';return []
 proposed,fit=fit_observed_row(dict(objects=observed),row,budget);ev['fit']=fit;ids=[]
 for o in proposed:
  o['id']='CTV3-'+o['id'];o['source_evidence'].update(algorithm_detected=True,evidence_type='raw_profile_peak_on_independently_reinspected_path',source_path=path,interpretation=side)
  if try_add(o,key):ids.append(o['id'])
 ev['exported_ids']=ids;return ids
# Independent context inspection of all eight retired legacy paths.
ids=profile('LEFT-SHORT-AA','AA-F01648',[[10,957],[44,957]],[[396,1178],[430,1178]]);path_reviews.append(dict(legacy='BAND-AA-F01648-00',status='independent_visible_left_edge_reinspection',new_ids=ids,prior_wrong_point='source61 belongs adjacent MOS diffusion; do not reuse it'))
for target,x in [('AA-F01951',1855),('AA-F01952',1758)]:
 path_reviews.append(dict(legacy='BAND-'+target+'-00',status='old_locator_retired_material_source_still_unknown',new_ids=[],reason='isolated AA has no POLY owner and no independently matched distinct optical cut; do not borrow H1 row peaks'))
 a=object_polygon(aa[target]);unknown.append(dict(id='U-'+target,kind='unlocated_isolated_AA_CT_unknown',AA_target=target,layout_bounds=list(a.bounds),criticality='no_known_device_port_inferred',question_for_human=None))
for key,target,path,lay in [('H1','AA2-TOP-H1-AA-0',[[2800,5],[3500,14],[4700,26],[5200,36]],[[3000,277.0974],[5220,277.0974]]),('H2','AA2-TOP-H2-AA-0',[[30,73],[1800,78],[3500,98],[5000,119],[5250,123]],[[300,377],[5260,377]])]:
 profile(key+'-VISIBILITY',target,path,lay,False,'AA stripe visible but compact CT not independently distinguishable from continuous band / photographed-screen texture');path_reviews.append(dict(legacy='BAND-'+target+'-00',status='wrong_cross_row_locator_retired_CT_observability_unknown',new_ids=[],reason='do not turn continuous bright edge or photographed-screen modulation into cuts; H1 partly outside usable upper source margin'))
 unknown.append(dict(id='U-'+key,kind='guard_CT_observability_unknown',AA_target=target,layout_bounds=list(object_polygon(aa[target]).bounds),criticality='guard_body_metal_access_not_proven',question_for_human=None))
ids=profile('Q3B-GUARD','AA2-LEFT-GUARD-NETWORK-SHARED-GUARDS-4',[[879,3195],[1082,3189],[1279,3184]],[[1100.7202,3239.6125],[1480.42085,3239.6125]])
path_reviews.append(dict(legacy='BAND-AA2-LEFT-GUARD-NETWORK-SHARED-GUARDS-4-00',status='independent_row_relocalized_using_human_Q3B_reference',new_ids=ids))
ids=profile('Q3C-GUARD','AA2-TOP-STEP-2-AA-0',[[4850,380],[5109,381]],[[4825.0839,642],[5098,642]])
path_reviews.append(dict(legacy='BAND-AA2-TOP-STEP-2-AA-0-02',status='independent_row_relocalized_using_human_Q3C_reference',new_ids=ids))
CX='AA2-UPPER-COMPLEX-GUARD-AA-0-split01';ids=profile('COMPLEX-LEFT',CX,[[15,819],[400,818],[875,819]],[[332,1052.659703510893],[1160,1052.659703510893]])
ids+=profile('COMPLEX-RIGHT',CX,[[4090,829],[4700,831],[5185,835]],[[4090,1052.659703510893],[5230,1052.659703510893]])
path_reviews.append(dict(legacy='BAND-'+CX+'-00',status='new_independent_interval_hypotheses_partial_recovery_central_assignment_unknown',new_ids=ids,not_whole_path_PASS=True))
unknown.append(dict(id='U-COMPLEX-CENTRE',kind='adjacent_guard_source_ownership_not_resolved',AA_targets=[CX,'AA2-UPPER-INNER-B-AA-0'],layout_bounds=[1186,1028,4071,1061],criticality='do_not_merge_adjacent_guard_nets',question_for_human='Adjacent upper guards have a very close photographed bright band. Preserve ambiguity rather than using one cut for both guards.'))
# Propagate counterexamples to the complete competing unaccepted neighbour recipe.
profile('G61-GUARD-TOP','AA2-LEFT-GUARD-NETWORK-SHARED-GUARDS-2',[[879,3058],[1082,3054],[1279,3047]],[[1100.7202,3126.9346],[1480.42085,3126.9346]])
profile('TOP-STEP1-UPPER','AA2-TOP-STEP-1-AA-0',[[4850,349],[5109,352]],[[4825,607],[5097,607]])
# Complete reinspection of the U10 guard frame after corner/source counterexamples.
profile('U10-GUARD-TOP','AA-G001',[[2220,1125],[2326,1124]],[[2340.5,1331.5],[2446.5,1331.5]])
profile('U10-GUARD-BOTTOM','AA-G001',[[2230,1707],[2335,1707]],[[2340.5,1870],[2446.5,1870]])
profile('U10-GUARD-LEFT','AA-G001',[[2212,1140],[2216,1300],[2220,1500],[2225,1690]],[[2340.5,1348],[2340.5,1853]])
profile('U10-GUARD-RIGHT','AA-G001',[[2332,1140],[2339,1300],[2343,1500],[2347,1690]],[[2446.5,1348],[2446.5,1853]])
# One corner cut is sufficient for the unaccepted overlapping corner hypotheses; no double export.
q=rd(V1/'quarantined-observations-v1.json')['objects'];corner=next(z['candidate'] for z in q if z['candidate']['id']=='CTX-CTT-BAND-AA-G004-00-S000');try_add(copy.deepcopy(corner),'G004-corner_keep_top_row_phase_not_overlapping_vertical_copy')
# Access audit drives source checks; an unobserved diffusion region is NOT required to contain a CT.
initial=audit_terminal_access(working+new,mat);gaps=[r for r in initial['diffusion_regions'] if not r['contact_ids']];AACT=defaultdict(list);GCT=defaultdict(list)
for o in working+new:
 if o.get('AA_target'):AACT[o['AA_target']].append(o)
 if o.get('POLY_target'):GCT[o['POLY_target']].append(o)
port_checks=[]
for ix,region in enumerate(gaps):
 target=region['AA_target'];gs=[poly[k] for k in region['gate_ids']];gs=sorted(gs,key=lambda g:Polygon(g['layout_outline']).centroid.x);x1,y1,x2,y2=region['layout_bounds'];lx=(x1+x2)/2;ly=(y1+y2)/2;centers=np.array([Polygon(g['layout_outline']).centroid.x for g in gs]);tips=[]
 for g in gs:
  points=[o['source_evidence']['native_center'] for o in GCT.get(g['id'],[])];tips.append(np.mean(points,axis=0) if points else np.array(Polygon(g['native_outline']).centroid.coords[0]))
 tips=np.array(tips);pidx=int(np.argmin(abs(centers-lx)));g=gs[pidx];delta=lx-centers[pidx];existing=AACT[target]
 if len(gs)==1 and existing:
  valid=[o for o in existing if (o['layout_center'][0]-centers[0])*delta<0]
  offset=np.median([abs(o['source_evidence']['native_center'][0]-tips[0,0]) for o in valid]) if valid else 26
  nx=tips[0,0]+np.sign(delta)*max(16,min(35,offset))
 elif len(gs)>1:
  if lx<centers[0]:nx=tips[0,0]-(tips[1,0]-tips[0,0])*(centers[0]-lx)/(centers[1]-centers[0])
  elif lx>centers[-1]:nx=tips[-1,0]+(tips[-1,0]-tips[-2,0])*(lx-centers[-1])/(centers[-1]-centers[-2])
  else:nx=float(np.interp(lx,centers,tips[:,0]))
 else:nx=tips[pidx,0]+delta
 source_y=[o['source_evidence']['native_center'][1] for o in existing]
 # Prefer this body's independent CT row. Body midpoint is only a bounded locator when absent.
 ny=float(np.median(source_y)) if source_y else Polygon(g['native_outline']).centroid.y
 if g['id'].startswith('G65'):ny=3623-(nx-923)*.026
 if g['id'].startswith('G66'):ny=3754-(nx-931)*.027
 radius=12 if len(gs)==1 else max(4,min(11,(x2-x1)/3));bb=[max(0,int(nx-radius)),max(0,int(ny-7)),min(gray.shape[1],int(nx+radius+1)),min(gray.shape[0],int(ny+8))]
 if bb[2]<=bb[0] or bb[3]<=bb[1]:port_checks.append(dict(region=region,status='source_locator_outside_photo'));continue
 # Named edge windows were independently inspected after the broad locator failed or
 # crossed into the neighbouring device. These are observations, not blank grid slots.
 explicit_rois={
  ('AA-F01613',0):[720,1236,738,1250],
  ('AA-F01649',8):[550,943,571,966],
  ('AA2-LEFT-GUARD-NETWORK-LOWER-LEFT-CELLS-ROW3-AA7-0',1):[1450,3600,1475,3619],
  ('AA2-LEFT-GUARD-NETWORK-LOWER-LEFT-CELLS-ROW3-AA8-0',0):[1478,3600,1493,3617],
  ('AA2-LEFT-GUARD-NETWORK-LOWER-LEFT-CELLS-BRANCH-AA3-0',2):[1091,3494,1108,3517],
 }
 idx=int(region['id'].rsplit('D',1)[1]);bb=explicit_rois.get((target,idx),bb)
 ev=inspect_peak('V3-PORT-'+str(ix),bb)
 # New CT gets an observed row phase where possible, never a new synthetic full array.
 if existing:ly=min(max(float(np.median([o['layout_center'][1] for o in existing])),y1+3.5),y2-3.5)
 o=ct('CTV3-PORT-'+str(ix),target,[lx,ly],ev);added=try_add(o,'diffusion_access_reinspection:'+region['id']);port_checks.append(dict(region=region,status='observed_candidate_added' if added else candidate_decisions[-1]['decision'],candidate_id=o['id'],source_roi=bb))
# Review all old twenty residual observations explicitly; none silently disappear from evidence.
oldq={z['candidate']['id']:z for z in q};residual_items=[]
for d in rd(P/'prior-observation-disposition-v1.json')['objects']:
 if d['disposition']!='technical_source_or_geometry_check_retained':continue
 z=oldq[d['observation_id']];o=z['candidate'];why='retired_unsupported_optical_observation' if not o['source_evidence']['supported'] else 'superseded_by_independent_port_or_guard_reinspection_no_automatic_old_slot_release'
 residual_items.append(dict(id=o['id'],disposition=why,prior_reasons=z['reasons'],candidate=o))
assert len(path_reviews)==8 and len(residual_items)==20
review['authorized_new_contact_ids']=[o['id'] for o in new];wr(B/'authorization-v1.json',review)
# Reapply corrections with the final immutable authorization reference in their histories.
working=apply_source_correspondence_corrections([o for o in parent if o['id'] not in {c['id'] for c in changes}],corrections,review['authorized_source_correspondence_ids'],ref(B/'authorization-v1.json'))
allobs=working+new;source_points=np.array([o['source_evidence']['native_center'] for o in allobs]);source_conflicts=[]
for i,j in cKDTree(source_points).query_pairs(3):
 a,z=allobs[i],allobs[j]
 if i<len(working) and j<len(working):continue
 if a.get('AA_target',a.get('POLY_target'))!=z.get('AA_target',z.get('POLY_target')):source_conflicts.append([a['id'],z['id']])
assert not source_conflicts,source_conflicts
wr(B/'source-ownership-check-v1.json',dict(status='PASS_for_new_observations',radius_px=3,conflicts=source_conflicts,old_protected_points_not_redeclared_as_physical_truth=True))
report=audit_contacts(working+new,mat,budget);assert report['status']=='PASS',json.dumps(report)[:1800]
wr(B/'new-contacts-v1.json',dict(objects=new));wr(B/'unknown-sites-v1.json',dict(sites=[],unknown_scopes=unknown,not_hypothetical_hole_slots=True));wr(B/'source-reinspection-v1.json',dict(paths=path_reviews,profiles=profiles,local_optical_observations=optical,all8_legacy_recipes_retired_not_claimed_physically_complete=True));wr(B/'residual20-disposition-v1.json',dict(objects=residual_items));wr(B/'candidate-decisions-v1.json',dict(objects=candidate_decisions));wr(B/'port-source-checks-v1.json',dict(regions=port_checks));wr(B/'preflight-geometry-v1.json',report)
oldspec=rd(P/'spec-v1.json');spec=dict(operation='apply_local_review_revision',audit_terminal_access=True,inputs=dict(materials=ref(P/'material-model-v1.json'),contacts=ref(P/'model-v1.json'),parent_spec=ref(P/'spec-v1.json'),photo=ref('data/test_chip/tile_full/poly.jpg'),human_review=ref(B/'authorization-v1.json'),new_contacts=ref(B/'new-contacts-v1.json'),unknown_sites=ref(B/'unknown-sites-v1.json'),source_reinspection=ref(B/'source-reinspection-v1.json'),residual20=ref(B/'residual20-disposition-v1.json'),port_checks=ref(B/'port-source-checks-v1.json'),prior_decisions=ref(P/'human-review-v1.json')),budget=budget,material_changes=dict(objects=[],AA_objects=[]),contact_changes=changes,source_correspondence_corrections=corrections,review_images=[],cases=[],review_title='CT工作层全幅收口：来源清理、端口证据与整体验收',review_notes='保留已审结构；新CT须有原图支持。未知扩散区域不按规则补孔，所有未知单列；本页是整体工作层候选，尚未获得本轮整体批准。')
# Full scene remains one shared coordinate space; tiles are review windows, not separate extractions.
for c in rd(V1/'spec-v1.json')['cases']:
 if c['id'] in ['Q1','Q2','Q3A','Q3B','Q3C']:continue
 c=copy.deepcopy(c);c.pop('additional_modes',None);c['scope']='统一全幅模型的复核窗口；灰色为保留记录，蓝／紫为本轮候选；来源未知用范围标记，不补虚拟孔。';spec['cases'].append(c)
for c in oldspec['cases']:
 c=copy.deepcopy(c);c['scope']='已完成的Q1/Q2/Q3裁决原样继承，此处只供前后抽查，不要求重审。';spec['cases'].append(c)
spec['cases'].append(dict(id='U',title='上方近邻环来源未知范围（保留完整器件上下文）',source_bbox=[800,690,4250,1030],layout_bbox=[1060,820,4210,1245],scope='两条近邻环不能借同一亮点导出两个CT或推断相连；保留未知，供整体验收决定是否需要进一步定位。'))
wr(B/'spec-v1.json',spec)
print(json.dumps(dict(new=len(new),retired=len(changes),source_corrections=len(corrections),total=len(working)+len(new),path_new_counts={x['legacy']:len(x['new_ids']) for x in path_reviews},port_checked=len(port_checks),port_new=sum(x['status']=='observed_candidate_added' for x in port_checks),new_decisions=Counter(o['decision'] for o in candidate_decisions),geometry=report['status']),ensure_ascii=False))
