"""Prepare a bounded four-gate patch and evidence-linked CT limitations.
Invocation: PYTHONPATH=. .venv/bin/python /tmp/prepare_ct_final_v5.py
Audit recipe only; execution uses the existing ct_transfer CLI. Photos stay immutable.
"""
from pathlib import Path
import copy
import hashlib
import json

import cv2
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import Polygon
from shapely.ops import unary_union

from silicon_eye.ct_joint_reconstruction import audit_contacts
from silicon_eye.geometry_reconstruction import object_polygon
from silicon_eye.aa_completion import source_polygon

B=Path('benchmarks/ct-work-layer-final-v5');B.mkdir(exist_ok=True)
P=Path('benchmarks/ct-work-layer-reviewed-v4')
def rd(p):return json.loads(Path(p).read_text())
def wr(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
assert not (B/'freeze-manifest-v1.json').exists()
for name,h in rd(P/'freeze-manifest-v1.json')['locked_files'].items():assert sha(P/name)==h
review=dict(date='2026-10-21',user_instruction_verbatim='完成这三项后收口',
            authorized_scope=['four-gate local POLY revision and CT completion','remaining source limitations review','whole-work-layer quality review and engineering closeout'],
            four_gate_count=dict(status='AI_visual_recheck_supported_by_four_caps_and_five_diffusion_columns',
                                 user_request='确认蓝框1～4是否就是全部四条栅',
                                 not_relabelled_as_new_human_pixel_or_count_annotation=True),
            prior_R1_R2_review_ref=ref(P/'human-review-v1.json'),
            full_physical_CT_recovery_not_claimed=True,whole_frame_human_visual_approval=False)
wr(B/'human-review-v1.json',review)
mat=rd(P/'material-model-v1.json');parent=rd(P/'model-v1.json')['objects'];budget=rd(P/'spec-v1.json')['budget']
oldids=[f'G06-P{i:02}' for i in range(6,11)]
retired=[g for g in mat['objects'] if g['id'] in oldids]
assert len(retired)==5 and all(g['acceptance']['joint_geometry']=='candidate' for g in retired)
assert not any(o.get('POLY_target') in oldids for o in parent)
patch=[]
for index,(lx,nx) in enumerate(zip(np.linspace(3770,3931,4),[3771,3816,3871,3922],strict=True),1):
    patch.append(dict(id=f'G06R-P{index:02}',material='POLY',kind='MOS_gate_body',group_id='G06R',
                      AA_target='AA-F01804',layout_outline=[[float(lx-16),431],[float(lx+16),431],[float(lx+16),546],[float(lx-16),546]],
                      native_outline=[[nx-18,177],[nx+18,177],[nx+18,322],[nx-18,322]],
                      source_scope='poly source rectangle is an AI locator, not exact material pixel boundary',
                      observed_upper_terminal=dict(native_center_locator=[nx,190],band_bbox=[nx-22,174,nx+23,212]),
                      terminal_status='upper_side_inherited_human_R1B_confirmation',
                      geometry_method='four_observed_caps_and_five_SD_columns_joint_regular_reconstruction',
                      supersedes_group_material_ids=oldids,
                      acceptance=dict(material='AI_visual_rechecked_supported_by_source_and_prior_R1B_side',joint_geometry='AI_checked_candidate',electrical='unknown'),
                      review_ref=ref(B/'human-review-v1.json')))
materials=copy.deepcopy(mat);materials['objects']=[g for g in materials['objects'] if g['id'] not in oldids]+patch
changes=[dict(id=g['id'],before=g,after=None) for g in retired]+[dict(id=g['id'],before=None,after=g) for g in patch]
gray=cv2.imread('data/test_chip/tile_full/poly.jpg',0);smooth=cv2.GaussianBlur(gray,(5,5),1).astype(float);residual=smooth-cv2.GaussianBlur(smooth,(0,0),4)
new=[];observations=[]
def peak(key,bb):
    l,t,r,b=map(int,bb);z=residual[t:b,l:r];dy,dx=np.unravel_index(z.argmax(),z.shape);x,y=int(l+dx),int(t+dy)
    ev=dict(native_center=[x,y],source_native_center_xy=[x,y],source_roi=[l,t,r,b],source_observation_id=key,
            supported=bool(smooth[y,x]>=205 and residual[y,x]>=20),peak_gray=float(smooth[y,x]),local_residual=float(residual[y,x]),
            evidence_type='bounded_optical_peak_with_AI_four_gate_correspondence_and_human_upper_terminal_side',algorithm_detected=True)
    observations.append(dict(id=key,source_evidence=ev));assert ev['supported'],ev
    return ev
def contact(key,target,kind,xy,ev,family,column,row):
    x,y=map(float,xy)
    new.append(dict(id=key,layer='CT',family=family,column=column,row=row,landing_material=kind,
                    **{('POLY_target' if kind=='POLY' else 'AA_target'):target},layout_center=[x,y],
                    layout_outline=[[x-2.5,y-2.5],[x+2.5,y-2.5],[x+2.5,y+2.5],[x-2.5,y+2.5]],
                    source_frame='poly',source_evidence=ev,status='AI_final_work_layer_geometry_with_scoped_human_side_confirmation',M1_enclosure='unknown',net_id=None))
for g in patch:
    nx=g['observed_upper_terminal']['native_center_locator'][0];cx=Polygon(g['layout_outline']).centroid.x
    for col,(left,right,dx) in enumerate([(nx-18,nx,-6),(nx+1,nx+19,6)]):
        key=f'CTV5-GATE-{g["id"]}-{col}'
        contact(key,g['id'],'POLY',[cx+dx,435],peak(key,[left,174,right,212]),'V5-GATE-'+g['id'],col,0)
aa=next(a for a in materials['AA_objects'] if a['id']=='AA-F01804')
windows=sorted(object_polygon(aa).difference(unary_union([Polygon(g['layout_outline']) for g in patch])).geoms,key=lambda p:p.centroid.x)
assert len(windows)==5
for col,(w,nx) in enumerate(zip(windows,[3741,3792,3844,3892,3944],strict=True)):
    family='V5-SD-G06R'+('-INTERIOR' if 0<col<4 else '-EDGE'+str(col))
    for row in range(5):
        ny=217+row*15.5+(nx-3741)*.005;key=f'CTV5-SD-G06R-{col}-{row}'
        contact(key,aa['id'],'AA',[w.centroid.x,451+18.75*row],peak(key,[nx-6,int(ny-6),nx+7,int(ny+7)]),family,col,row)
allct=parent+new
audit=audit_contacts(allct,materials,budget);assert audit['status']=='PASS',str(audit)[:1800]
conflicts=[];newids={o['id'] for o in new}
for i,j in cKDTree([o['source_evidence']['native_center'] for o in allct]).query_pairs(3):
    x,y=allct[i],allct[j]
    if {x['id'],y['id']}&newids:conflicts.append([x['id'],y['id']])
assert not conflicts,conflicts

# Reinspection distinguishes actual missing access from limited visibility or a body
# fragment whose terminal belongs to the historical reviewed circuit representation.
legacy=rd('benchmarks/aa-full-frame-workflow-v1/model-v1.json')
limits=[]
for old in rd(P/'unknown-sites-v1.json')['unknown_scopes']:
    if old['id']=='U-R1B-RIGHT-COUNT':continue
    u=copy.deepcopy(old);u.update(status='CT_not_reconstructed_source_limit_retained',
                                 no_CT_is_not_proven_absence=True,mandatory_human_action_now=False,
                                 tracing_policy='do_not_infer_CT_or_M1_connection_here',
                                 reopen_when='new_observation_or_validated_local_correspondence_or_requested_trace_intersects_scope')
    if u['AA_target'] in ['AA-F01951','AA-F01952']:
        oldaa=next(a for a in legacy['objects'] if a['id']==u['AA_target']);u['AA_legacy_locator_native_bounds']=list(source_polygon(oldaa,legacy).bounds)
        u['reinspection']='Legacy global locator does not independently establish a distinct isolated AA body or its POLY-photo correspondence; no associated gate or known device access. Preserve AA candidate, do not borrow a nearby guard peak.'
        u['evidence_inputs']=[ref('data/test_chip/tile_full/aa.jpg'),ref('data/test_chip/tile_full/poly.jpg'),ref('benchmarks/aa-full-frame-workflow-v1/model-v1.json')]
        u['native_review_windows']={'aa':[1730,180,2120,410],'poly':[1450,0,2250,330]}
    else:
        u['reinspection']='Visible long optical band contains screen moire / unresolved bright texture; compact CT cannot be separated reliably. M1 continuity cannot prove a cut through the dielectric.'
        u['evidence_inputs']=[ref('data/test_chip/tile_full/aa.jpg'),ref('data/test_chip/tile_full/poly.jpg'),ref('data/test_chip/tile_full/m1.jpg')]
        u['native_review_windows']={'aa':[1300,160,2250,410],'poly':[1300,0,2250,150],'m1':[1300,160,2250,360]}
        if u['id']=='U-H1':u['reinspection']+=' The POLY photo partly clips the upper band.'
    limits.append(u)
limits.append(dict(id='L-CLIPPED-AA-F01744',kind='device_body_CT_source_outside_current_photo',AA_target='AA-F01744',
                   layout_bounds=[354,522,456,574],no_CT_is_not_proven_absence=True,status='excluded_from_source_complete_claim',
                   tracing_policy='keep_terminal_access_unknown_here',mandatory_human_action_now=False,
                   evidence_ref=ref('benchmarks/ct-work-layer-closeout-v3/port-source-checks-v1.json')))
unknown=dict(sites=[],unknown_scopes=limits,not_hypothetical_hole_slots=True)
authorization=dict(human_review_ref=ref(B/'human-review-v1.json'),authorized_material_ids=oldids+[g['id'] for g in patch],
                   authorized_contact_ids=[],authorized_source_correspondence_ids=[],authorized_new_contact_ids=[o['id'] for o in new],
                   scope='User-authorized three-task completion; AI exact geometry and source measurements remain distinct from human pixel approval')
wr(B/'authorization-v1.json',authorization);wr(B/'new-contacts-v1.json',dict(objects=new));wr(B/'unknown-sites-v1.json',unknown)
wr(B/'optical-observations-v1.json',dict(objects=observations,unchanged_thresholds=dict(min_gray=205,min_residual=20),source_conflicts_within3px=conflicts))
wr(B/'retired-material-records-v1.json',dict(objects=retired,reason='five old AI template records superseded by four source-supported gates; no guessed one-to-one alias',replacement_ids=[g['id'] for g in patch]))
wr(B/'preflight-geometry-v1.json',audit)
inventory=dict(photos=[ref(p) for p in sorted(Path('data/test_chip/tile_full').glob('*.jpg'))],unaltered_raw_evidence=True)
wr(B/'input-inventory-v1.json',inventory)
cases=[dict(id='RIGHT4',title='右上末段：四栅及五列源漏CT',source_bbox=[3500,110,4120,375],layout_bbox=[3700,410,4000,565],
            scope='四组原图上端栅亮条对应四条规则POLY；每栅两候选CT，五列源漏各五个候选。原图和规则图为独立坐标，不做未经验证回投影。'),
       dict(id='LIMITS',title='照片上沿受限范围：不补造孔',source_bbox=[1300,0,2250,330],layout_bbox=[1550,255,2300,410],
            scope='两小AA和H1/H2长条保留来源限制；无CT不代表物理无孔，限制区域禁止自动推断连接。')]
spec=dict(operation='apply_local_review_revision',audit_terminal_access=True,
          inputs=dict(materials=ref(P/'material-model-v1.json'),contacts=ref(P/'model-v1.json'),parent_spec=ref(P/'spec-v1.json'),
                      photo=ref('data/test_chip/tile_full/poly.jpg'),AA_photo=ref('data/test_chip/tile_full/aa.jpg'),M1_photo=ref('data/test_chip/tile_full/m1.jpg'),
                      human_review=ref(B/'authorization-v1.json'),user_scope=ref(B/'human-review-v1.json'),new_contacts=ref(B/'new-contacts-v1.json'),
                      unknown_sites=ref(B/'unknown-sites-v1.json'),optical_observations=ref(B/'optical-observations-v1.json'),raw_inventory=ref(B/'input-inventory-v1.json')),
          budget=budget,material_changes=dict(objects=changes,AA_objects=[]),contact_changes=[],source_correspondence_corrections=[],review_images=[],cases=cases,
          review_title='CT工作层v1：四栅补齐与工程收口（保留受限范围）',
          review_notes='只修订已核清的右上四栅，保留全部父CT及无关材料。受限范围完整保留，不声称100%物理孔恢复。工程验收与整层人工像素批准分别记录。')
wr(B/'spec-v1.json',spec)
print(json.dumps(dict(new_CT=len(new),gate_CT=8,SD_CT=25,total=len(allct),POLY=len(materials['objects']),AA=len(materials['AA_objects']),geometry=audit['status'],limitations=len(limits)),ensure_ascii=False))
