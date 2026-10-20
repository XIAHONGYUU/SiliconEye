"""Prepare one review entry, scoped export spec and explicit human-decision gate."""
from pathlib import Path
import json,hashlib,copy,shutil
from collections import Counter
import numpy as np
from PIL import Image,ImageDraw
from shapely.geometry import Polygon
root=Path.cwd();b=Path('benchmarks/ct-full-frame-remaining-v1');p=Path('benchmarks/ct-lower-middle-mos-revision-v2');ctx=b/'source-context';ctx.mkdir(exist_ok=True)
def rd(p):return json.loads(Path(p).read_text())
def wr(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
mat=rd(p/'material-model-v1.json');new=rd(b/'selected-contacts-v1.json')['objects'];old=rd(p/'model-v1.json')['objects'];quarantine=rd(b/'quarantined-observations-v1.json')['objects'];photo=Image.open('data/test_chip/tile_full/poly.jpg');m1=Image.open('data/test_chip/tile_full/m1.jpg');cases=[];images=[]
inputs=dict(materials=ref(p/'material-model-v1.json'),contacts=ref(p/'model-v1.json'),parent_spec=ref(p/'spec-v1.json'),photo=ref('data/test_chip/tile_full/poly.jpg'),parent_acceptance=ref(p/'acceptance-v1.json'),human_review=ref(b/'authorization-v1.json') if (b/'authorization-v1.json').exists() else None,new_contacts=ref(b/'selected-contacts-v1.json'),unknown_sites=None,m1_photo=ref('data/test_chip/tile_full/m1.jpg'))
questions=[dict(id='Q1',title='左侧四管：真实栅端来源',question='四管/2×2结论保留，不重审数量。旧四个源框的端部取点与既有环及G18源记录重合，当前不能证明四管的真实栅端位置。请在本组原图指出任意一个真实栅端CT，或说明引出在上/下/侧；红叉只表示本组归属被拒绝，亮点本身仍可能是环或G18上的CT。',material_ids=['CL2-Q3-AA-F01613-01','CL2-Q3-AA-F01613-02','CL2-Q3-AA-F01614-01','CL2-Q3-AA-F01614-02'],blocks='four gate-terminal ownerships',status='needs_human_source_landmark'),dict(id='Q2',title='U10：两条细长POLY下端',question='旧紫色源框的端部与亮点没有可靠对应。两条细长POLY在下端分别引出，还是共用端部？请指出实际CT所在亮点；目前不补孔、不补POLY桥。',material_ids=['G68-P01','G68-P02'],blocks='two gate-terminal ownerships',status='needs_human_terminal_landmark'),dict(id='Q3',title='环与栅端的原图对应',question='A/B/C橙圈是AI从器件上下文辨认的栅端CT，蓝线标出相邻环参考。请核对它们与联合图中G/A的对应。源定位发生反例的7条AA路径已整段暂缓，确认材料对应后再补，不能只删冲突点宣称整段正确。',material_ids=['G07-P02','G62-P04','SG-U04-080'],deferred_source_paths=rd(b/'deferred-source-paths-v1.json')['families'],blocks='seven AA source-path correspondences',status='needs_human_crosscheck_correspondence')]
wr(b/'review-questions-v1.json',dict(status='HOLD_not_full_frame_acceptance',questions=questions,no_reapproval_of_parent7044=True,exact_CT_count_not_primary_human_task=True))
# Per-question reference images retain broad context and never project another unaligned photograph.
boxes={'Q1':[620,1100,1700,1510],'Q2':[2070,1300,2430,1770]};m1boxes={'Q1':[600,1240,1820,1900],'Q2':[1990,1190,2540,2020]}
for key,bb in boxes.items():
 c=photo.crop(bb);d=ImageDraw.Draw(c)
 if key=='Q1':
  for g in mat['objects']:
   if g['id'].startswith('CL2-Q3-AA'):
    l,t,r,bt=Polygon(g['native_outline']).bounds;d.rectangle((l-bb[0],t-bb[1],r-bb[0],bt-bb[1]),outline='#d6a4f4',width=2)
  for x in quarantine:
   o=x['candidate']
   if str(o.get('POLY_target','')).startswith('CL2-Q3-AA'):
    xx,yy=o['source_evidence']['native_center'];xx-=bb[0];yy-=bb[1];d.line((xx-5,yy-5,xx+5,yy+5),fill='#ff755f',width=2);d.line((xx-5,yy+5,xx+5,yy-5),fill='#ff755f',width=2)
  d.text((15,15),'OLD source boxes / rejected picks only - real gate terminal required',fill='#ffcf55')
 else:
  for g in mat['objects']:
   if g['id'] in ['G68-P01','G68-P02']:
    l,t,r,bt=Polygon(g['native_outline']).bounds;d.rectangle((l-bb[0],max(0,t-bb[1]),r-bb[0],bt-bb[1]),outline='#d6a4f4',width=2);d.text((l-bb[0],bt-bb[1]+5),g['id'],fill='#ffcf55')
  d.text((12,12),'OLD native locator - not confirmed CT or a POLY bridge',fill='#ffcf55')
 c.save(ctx/f'{key}-inspection.png');m1.crop(m1boxes[key]).save(ctx/f'{key}-m1.png')
# Three ambiguous mappings, now explicitly inspected as gate tips; neighbouring guard references remain candidate.
heldsource=rd(b/'all-proposed-repaired-v1.json')['objects'];Q3=[]
for key,gid in [('Q3A','G07-P02'),('Q3B','G62-P04'),('Q3C','SG-U04-080')]:
 o=next(o for o in heldsource if o.get('POLY_target')==gid and '-top-' in o['id']);x,y=o['source_evidence']['native_center'];bb=[max(0,int(x)-130),max(0,int(y)-85),min(photo.width,int(x)+150),min(photo.height,int(y)+140)];c=photo.crop(bb);d=ImageDraw.Draw(c);cx=x-bb[0];cy=y-bb[1];d.ellipse((cx-4,cy-4,cx+4,cy+4),outline='#ffb45b',width=2);d.text((cx+7,cy),'G',fill='#ffb45b');d.line((cx-80,cy-32,cx+80,cy-32),fill='#56baff',width=2);d.text((cx-85,cy-49),'A guard reference (candidate)',fill='#56baff');c.save(ctx/f'{key}-inspection.png')
 g=next(g for g in mat['objects'] if g['id']==gid);l,t,r,bt=Polygon(g['layout_outline']).bounds;Q3.append((key,gid,bb,[max(0,l-130),max(0,t-95),r+130,bt+140]))
# Cases prioritize actual decision gates, then optional full-frame spot-checking.
for key,title,sb,lb in [('Q1','Q1：旧四框对应冲突，需真实栅CT锚点',boxes['Q1'],[960,1350,1620,1810]),('Q2','Q2：U10两条细POLY端部待定位',boxes['Q2'],[2260,1320,2525,1900])]:
 c=dict(id=key,title=title,source_bbox=sb,layout_bbox=lb,scope='只裁决端部来源，不重审数量或已批孔；紫框是旧源定位，不是新的已审物理边界。',additional_modes=[['inspection','png','宽视野原图＋旧源框／被拒绝取点'],['m1-context','png','M1独立坐标宽视野（未在此页精确配准）']]);cases.append(c)
 for mode,file in [('inspection',ctx/f'{key}-inspection.png'),('m1-context',ctx/f'{key}-m1.png')]:
  k=key+'_'+mode;inputs[k]=ref(file);images.append(dict(input_key=k,output_name=f'{key}-{mode}.png'))
for key,gid,sb,lb in Q3:
 cases.append(dict(id=key,title=f'{key}：{gid} 栅端G与上方环A的对应',source_bbox=sb,layout_bbox=lb,scope='橙G为AI观察的栅端；蓝A是相邻环原图参考。两种图各自保留坐标，禁止盲投影。对应失败的整条新AA路径不进入CT输出。',additional_modes=[['inspection','png','原图G／A参考（保留完整相邻器件）']]))
 k=key+'_inspection';inputs[k]=ref(ctx/f'{key}-inspection.png');images.append(dict(input_key=k,output_name=f'{key}-inspection.png'))
for key,title,sb,lb in [('O','全幅：已审CT保持，新增候选与待决范围分开',[0,0,5712,4284],[200,120,5650,4550]),('T1','上方左／中密集MOS：源漏与栅端候选',[0,70,2700,850],[230,300,2910,1150]),('T2','上方右侧密集MOS及电阻W01端部',[2400,50,5200,900],[2550,260,5310,1190]),('T3','上部下方两长排小MOS与可见环',[0,790,5250,1190],[230,1000,5320,1490]),('L','左下小MOS与环的剩余可见部分',[780,2970,1630,3840],[1020,3070,1770,3870]),('R','右下12宽MOS：只在独立观察端生成栅CT',[3160,3240,4790,3720],[3240,3430,4820,3850])]:
 cases.append(dict(id=key,title=title,source_bbox=sb,layout_bbox=lb,scope='灰蓝为原7044工作快照；蓝／紫为新增AA／POLY CT候选。新图不代表全幅验收；未决路径与未确定孔不补入。'))
wr(b/'unknown-sites-v1.json',dict(sites=[],scope='Unresolved source-path/terminal ownership is listed in explicit review cases; no lattice square is invented as a pending physical cut'))
authorization=dict(date='2026-10-20',user_instruction_verbatim='将CT层次剩余的工作进行完全后看是否还有需要我批准的地方',scope='Permission to inspect remaining photographs and generate candidates; NOT human acceptance of new identities/geometry',authorized_material_ids=[],authorized_contact_ids=[],authorized_new_contact_ids=[o['id'] for o in new],preserve_parent7044=True,physical_human_decisions_pending=['Q1','Q2','Q3'])
wr(b/'authorization-v1.json',authorization);inputs['human_review']=ref(b/'authorization-v1.json');inputs['unknown_sites']=ref(b/'unknown-sites-v1.json')
for key,path in [('questions',b/'review-questions-v1.json'),('quarantine',b/'quarantined-observations-v1.json'),('material_coverage',b/'final-material-coverage-v1.json'),('AA_band_audit',b/'AA-band-audit-v1.json'),('source_repair',b/'source-correspondence-repair-v2.json'),('deferred_paths',b/'deferred-source-paths-v1.json'),('SD_recovery',b/'SD-recovery-v1.json'),('last_SD',b/'last-SD-body-inspection-v1.json'),('terminal_direction_review',b/'AI-terminal-direction-review-v1.json')]:inputs[key]=ref(path)
spec=dict(operation='apply_local_review_revision',inputs=inputs,budget=rd(p/'spec-v1.json')['budget'],material_changes=dict(objects=[],AA_objects=[]),contact_changes=[],review_images=images,cases=cases,review_title='CT剩余范围：候选已补查，3项关键裁决待完成',review_notes='原7044条记录和全部AA/POLY对象不动。新增来源候选仅导出整组几何合格子集；源归属反例会整条暂缓对应的新AA路径，全部原观察保留。全幅状态HOLD，不把安全子集PASS当作整层完成。请优先看Q1/Q2/Q3；其余范围供抽查，不要求逐孔审批。')
wr(b/'spec-v1.json',spec)
counts=Counter(o['landing_material'] for o in new);wr(b/'stage-gate-v1.json',dict(status='HOLD_human_terminal_and_source_correspondence_decisions',safe_subset_geometry='PASS',prior_contact_count=7044,new_candidate_count=len(new),new_by_landing=dict(counts),working_snapshot_count=len(old)+len(new),inspected_unreferenced_POLY_materials=409,new_direct_CT_references=401,historical_body_fragments_retained=2,remaining_unresolved_terminal_material_ids=rd(b/'final-material-coverage-v1.json')['unresolved_ids'],quarantined_candidate_count=len(quarantine),quarantined_is_not_missing_hole_count=True,deferred_path_count=len(rd(b/'deferred-source-paths-v1.json')['families']),AA_disposition=dict(prior_body_CT_scopes=55,new_body_families_inspected=115,prior_guard_scopes_preserved=12,new_guard_or_strip_objects_inspected=29,dummy_objects_no_CT_inferred=108,compact_unassociated_AA_unknown=11,neighbour_edge_objects_not_extended=5),all335_AA_objects_have_disposition=True,all695_POLY_objects_have_disposition=True,whole_frame_human_accepted=False,physical_PDK_DRC=False,blocking_human_cases=['Q1','Q2','Q3'],not_repeating_exact_hole_count_review=True))
prov=b/'provenance';prov.mkdir(exist_ok=True)
for src in ['/tmp/prepare_ct_remaining.py','/tmp/complete_ct_context.py','/tmp/repair_G49_ct.py','/tmp/finalize_ct_candidates.py','/tmp/repair_sparse_SD_ct.py','/tmp/recover_last_SD_bodies.py','/tmp/refine_G49_frame_ct.py']:shutil.copyfile(src,prov/Path(src).name)
shutil.copyfile('/tmp/compact-AA-source-context.json',b/'compact-AA-source-locators-v1.json');shutil.copyfile('/tmp/compact-AA-source-context.jpg',ctx/'compact-AA-context.jpg')
print('new',len(new),'total',len(old)+len(new),'by_material',dict(counts),'cases',len(cases),'HOLD Q1/Q2/Q3')
