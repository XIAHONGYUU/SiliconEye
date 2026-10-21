"""Prepare a bounded CT adjudication revision; run from repo with .venv Python.
Requires immutable v1 inputs and the user's 2026-10-21 decisions. Audit recipe only.
"""
from pathlib import Path
import copy,json,hashlib
import cv2,numpy as np
from scipy.signal import find_peaks
from shapely.geometry import Polygon,box
from silicon_eye.ct_joint_reconstruction import audit_contacts
from silicon_eye.ct_transfer import apply_source_correspondence_corrections
B=Path('benchmarks/ct-full-frame-adjudication-v2');P=Path('benchmarks/ct-full-frame-remaining-v1');B.mkdir(exist_ok=True);assert not (B/'model-v1.json').exists()
def rd(p):return json.loads(Path(p).read_text())
def wr(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
verbatim='''Q1：左侧四管栅极CT从下端饮醋，上方红X为环上的CT
Q2：共用下端poly引出，实际在poly上的CT在下方两poly连接处
Q3A：G是栅端gate,且没有从poly下方引出。蓝色A为上方inside的环，靠近栅极A,联合图对应A应该是下面那条环
Q3B：G与A身份关系对应正确
Q3C：G与A身份关系对应正确。
裁决完成'''
q1ids=['CL2-Q3-AA-F01613-01','CL2-Q3-AA-F01613-02','CL2-Q3-AA-F01614-01','CL2-Q3-AA-F01614-02']
review=dict(date='2026-10-21',user_instruction_verbatim=verbatim,source='human_message_in_current_chat',decisions=[dict(id='Q1',status='human_decided',gate_CT_side='bottom',upper_red_X_role='guard_AA_CT',material_ids=q1ids,exact_peak_count_and_coordinates='AI_reinspection_candidates_not_human_pixel_truth'),dict(id='Q2',status='human_decided',members=['G68-P01','G68-P02'],connection='shared_bottom_POLY',CT_role='on_shared_bottom_connection',exact_outline_and_count='candidate'),dict(id='Q3A',status='human_decided',G='top_gate_terminal',bottom_gate_CT=False,A='inner_guard_closer_to_gate',layout_A_target='AA2-TOP-H3-AA-0'),dict(id='Q3B',status='human_correspondence_confirmed',G='gate_terminal',A='guard_reference'),dict(id='Q3C',status='human_correspondence_confirmed',G='gate_terminal',A='guard_reference')],scope='Semantic/source-correspondence decisions only; not blanket acceptance of v1 candidates or new geometry',authorized_material_ids=['G68-BOTTOM-BUS-01'],authorized_contact_ids=[],authorized_source_correspondence_ids=[],authorized_new_contact_ids=[],whole_frame_human_accepted=False)
# Persist original statement before any measurements or model changes.
wr(B/'human-review-v1.json',review)
mat=rd(P/'material-model-v1.json');parent=rd(P/'model-v1.json')['objects'];byid={o['id']:o for o in parent};poly={o['id']:o for o in mat['objects']};budget=rd(P/'spec-v1.json')['budget'];gray=cv2.imread('data/test_chip/tile_full/poly.jpg',0);sm=cv2.GaussianBlur(gray,(5,5),1).astype(float);res=sm-cv2.GaussianBlur(sm,(0,0),4)
obs=[]
def inspect(tag,bb,distance=7):
 l,t,r,b=bb;score=np.maximum(sm[t:b,l:r]-185,0).mean(axis=1);y=t+int(score.argmax());xp=sm[max(t,y-1):min(b,y+2),l:r].mean(axis=0);peaks,_=find_peaks(xp,height=190,distance=distance,prominence=5);result=[(int(l+i),int(y)) for i in peaks if res[y,l+i]>=18];obs.append(dict(id=tag,source_roi=bb,selected_row=y,peaks=[dict(native_center=list(pt),gray=float(sm[pt[1],pt[0]]),residual=float(res[pt[1],pt[0]])) for pt in result],source_photo_ref=ref('data/test_chip/tile_full/poly.jpg'),status='AI_bounded_optical_observations_not_human_pixel_labels'));return result
# Neighbouring G18 geometry was approved, but two optical-source row picks used the wrong devices.
# Reinspect G03 and G07 at the same TOP row as their neighbours, keeping every CT design field.
corrections=[]
for gid,bb in [('G18-P03',[885,1352,940,1372]),('G18-P07',[1190,1351,1245,1370])]:
 contacts=[o for o in parent if o.get('POLY_target')==gid];pts=inspect('reinspect-'+gid,bb)
 assert len(pts)>=len(contacts),(gid,pts)
 for old,pt in zip(contacts,pts,strict=False):
  after=copy.deepcopy(old['source_evidence']);after.update(native_center=list(pt),source_native_center_xy=list(pt),source_observation_id="ADJ-RELOCALIZE-"+old["id"],supported=True,source_roi=bb,peak_gray=float(sm[pt[1],pt[0]]),local_residual=float(res[pt[1],pt[0]]),evidence_type='AI_independent_reinspection_after_human_Q1_bottom_terminal_decision',native_locator_status='relocalized_top_terminal_bar_preserving_prior_evidence_in_history',algorithm_detected=True)
  corrections.append(dict(id=old['id'],before_source_evidence=copy.deepcopy(old['source_evidence']),after_source_evidence=after,reason='Q1 ownership counterexample prompted full G18 top-row consistency inspection; old pick lay on the preceding device row. Human approved topology retained; new exact source is an AI observation.'))
# Retire only NEW unaccepted bottom CT assignments where lower bright points are guard contacts.
# Human statement is explicit for P02; P01/P03 were independently checked in the same raw context.
retire=[o for o in parent if o.get('POLY_target','').startswith('G07-P') and '-bottom-' in o['id']]
contact_changes=[dict(id=o['id'],before=o,after=None,reason='Q3A explicit no-bottom-gate-CT for P02; same source guard bar independently inspected for sibling P01/P03',human_scope='P02 semantic decision; P01/P03 AI consistency repair') for o in retire]
review['authorized_contact_ids']=[o['id'] for o in retire];review['authorized_source_correspondence_ids']=[c['id'] for c in corrections]
# Shared bottom POLY patch is a new material ID; existing two fingers and all AA remain intact.
bus=dict(id='G68-BOTTOM-BUS-01',material='POLY',kind='shared_gate_terminal_bus',group_id='G68',member_POLY_ids=['G68-P01','G68-P02'],AA_target=None,native_outline=[[2248,1681],[2301,1681],[2301,1693],[2248,1693]],layout_outline=[[2359,1844],[2407,1844],[2407,1855],[2359,1855]],source_frame='poly',source_photo_ref=ref('data/test_chip/tile_full/poly.jpg'),geometry_method='human_confirmed_shared_bottom_connection_with_AI_candidate_regular_outline',acceptance=dict(joint_geometry='candidate_AI_outline_not_pixel_truth',connectivity='human_confirmed_shared_bottom_POLY'),net_id=None)
new=[]
def make(key,family,col,xy,pt,target,kind,role):
 x,y=map(float,xy);return dict(id=key,family=family,column=col,row=0,layer='CT',landing_material=kind,**{('POLY_target' if kind=='POLY' else 'AA_target'):target},layout_center=[x,y],layout_outline=[[x-2.5,y-2.5],[x+2.5,y-2.5],[x+2.5,y+2.5],[x-2.5,y+2.5]],source_frame='poly',source_evidence=dict(native_center=list(pt),peak_gray=float(sm[pt[1],pt[0]]),local_residual=float(res[pt[1],pt[0]]),supported=True,algorithm_detected=True,evidence_type='human_role_decision_plus_bounded_optical_candidate'),status='AI_geometry_candidate_under_human_semantic_decision',terminal_role=role,M1_enclosure='unknown',net_id=None)
for index,gid in enumerate(q1ids):
 nl,nt,nr,nb=Polygon(poly[gid]['native_outline']).bounds;pts=inspect('Q1-bottom-'+str(index+1),[int(nl)-3,1318,int(nr)+12,1334]);assert len(pts)==2,(gid,pts)
 l,t,r,b=Polygon(poly[gid]['layout_outline']).bounds
 for j,pt in enumerate(pts):new.append(make(f'CTA-Q1-G{index+1}-{j}',f'ADJ-Q1-G{index+1}',j,[(l+r)/2+(j-.5)*10,b-4],pt,gid,'POLY','gate_bottom'))
pts=inspect('Q2-shared-bottom',[2242,1676,2310,1701]);assert len(pts)==2,pts
for j,pt in enumerate(pts):new.append(make(f'CTA-Q2-BUS-{j}','ADJ-Q2-BUS',j,[2377+12*j,1849.5],pt,bus['id'],'POLY','shared_gate_bottom'))
# Restore the 16 held source/drain candidates only after role correspondence was resolved.
quarantine=rd(P/'quarantined-observations-v1.json')['objects']
for z in quarantine:
 o=z['candidate']
 if o.get('AA_target') in ['AA-F01613','AA-F01614']:
  assert z['reasons']==['Q1_material_source_correspondence_pending_do_not_export_dependent_SD'];new.append(copy.deepcopy(o))
review['authorized_new_contact_ids']=[o['id'] for o in new];wr(B/'human-review-v1.json',review);wr(B/'optical-reinspection-v1.json',dict(observations=obs,source_scope='only named patches, no full-frame rerun',counts_are_not_human_confirmed=True))
wr(B/'new-contacts-v1.json',dict(objects=new));wr(B/'unknown-sites-v1.json',dict(sites=[],note='No invented holes; unresolved source paths remain separate from resolved human questions'))
revised=copy.deepcopy(mat);revised['objects'].append(bus);corrected=apply_source_correspondence_corrections(parent,corrections,review['authorized_source_correspondence_ids'],ref(B/'human-review-v1.json'));retired={c['id'] for c in contact_changes};proposed=[o for o in corrected if o['id'] not in retired]+new
report=audit_contacts(proposed,revised,budget);wr(B/'preflight-geometry-v1.json',report);assert report['status']=='PASS',json.dumps(report,ensure_ascii=False)[:2500]
spec=dict(operation='apply_local_review_revision',inputs=dict(materials=ref(P/'material-model-v1.json'),contacts=ref(P/'model-v1.json'),parent_spec=ref(P/'spec-v1.json'),photo=ref('data/test_chip/tile_full/poly.jpg'),human_review=ref(B/'human-review-v1.json'),new_contacts=ref(B/'new-contacts-v1.json'),unknown_sites=ref(B/'unknown-sites-v1.json'),optical_reinspection=ref(B/'optical-reinspection-v1.json'),parent_stage_gate=ref(P/'stage-gate-v1.json')),budget=budget,material_changes=dict(objects=[dict(id=bus['id'],before=None,after=bus)],AA_objects=[]),contact_changes=contact_changes,source_correspondence_corrections=corrections,review_images=[],cases=[],review_title='CT裁决执行：Q1下端、Q2共用POLY、Q3内环对应',review_notes='五项语义裁决已记录。旧快照不覆盖；新精确几何仍是候选，整层完整性独立检查。')
oldspec=rd(P/'spec-v1.json');cases={c['id']:c for c in oldspec['cases']}
for key in ['Q1','Q2','Q3A','Q3B','Q3C']:
 c=copy.deepcopy(cases[key]);c.pop('additional_modes',None);c['title']={'Q1':'四管下端栅CT；上侧亮条为环CT','Q2':'下端共用POLY引出及连接处CT','Q3A':'仅上端栅CT；A改对应靠近栅极的内环','Q3B':'G栅端／A环对应已确认','Q3C':'G栅端／A环对应已确认'}[key];c['scope']='人审身份／方向与AI精确几何分开；原图与规则图各自保留坐标，不是盲投影。';spec['cases'].append(c)
wr(B/'spec-v1.json',spec)
wr(B/'human-decision-status-v1.json',dict(human_questions_resolved=['Q1','Q2','Q3A','Q3B','Q3C'],pending_human_questions=[],whole_frame_human_accepted=False,parent_ref=ref(P/'model-v1.json'),new_CT_count=len(new),retired_unaccepted_gate_CT=len(retire),old_source_coordinates_corrected_without_design_change=len(corrections),technical_source_paths_pending=rd(P/'deferred-source-paths-v1.json')['families'],path_count_correction='v1 text said seven; actual locked family list has eight. No historical record rewritten.',exact_new_geometry_human_accepted=False))
print('PREPARED',dict(new=len(new),retired=len(retire),source_corrections=len(corrections),total=len(proposed),geometry=report['status']))
