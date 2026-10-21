"""Package the full-frame CT working candidate, access inventory and final human source gate.
Run from repo with .venv Python after ct_transfer. Frozen inputs remain unchanged.
"""
from pathlib import Path
import json,hashlib,copy,shutil,re,xml.etree.ElementTree as ET
from html.parser import HTMLParser
from collections import Counter
from PIL import Image,ImageDraw
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from silicon_eye.ct_transfer import render_case
from silicon_eye.geometry_reconstruction import object_polygon
from silicon_eye.poly_closeout import svg
B=Path('benchmarks/ct-work-layer-closeout-v3');P=Path('benchmarks/ct-full-frame-adjudication-v2');A=Path('docs/assets/ct-work-layer-closeout-v3');R=Path('runs/ct-work-layer-closeout-v3a');A.mkdir(exist_ok=True)
def rd(p):return json.loads(Path(p).read_text())
def wr(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
s=rd(B/'spec-v1.json');mat=rd(R/'material-model.json');model=rd(R/'model.json');objects=model['objects'];report=rd(R/'report.json');access=rd(R/'terminal-access.json');old=rd(P/'model-v1.json')['objects'];oldby={o['id']:o for o in old};newby={o['id']:o for o in objects};retired={o['id'] for o in s['contact_changes']};corrected={o['id'] for o in s['source_correspondence_corrections']};added={o['id'] for o in rd(B/'new-contacts-v1.json')['objects']};assert report['status']=='PASS'
for key in set(oldby)&set(newby):
 if key not in corrected:assert oldby[key]==newby[key]
 else:
  q=copy.deepcopy(newby[key]);h=q['source_correspondence_history'];q['source_evidence']=h[-1]['before'];q['source_correspondence_history']=h[:-1]
  if not q['source_correspondence_history']:del q['source_correspondence_history']
  assert q==oldby[key]
assert set(oldby)-set(newby)==retired and set(newby)-set(oldby)==added
parentmat=rd(P/'material-model-v1.json');assert mat['objects']==parentmat['objects'] and mat['AA_objects']==parentmat['AA_objects']
prior=rd('benchmarks/ct-lower-middle-mos-revision-v2/model-v1.json')['objects'];assert all(newby[o['id']]==oldby[o['id']] for o in prior)
for r in s['inputs'].values():assert sha(r['path'])==r['sha256']
for n,h in rd(P/'verification-v1.json')['locked_files'].items():assert sha(P/n)==h
# Human source directions are still required for these distinct NEW groups, not old Q1/Q2/Q3.
blocked_groups=['G01','G02','G05','G06'];gates=[g for g in mat['objects'] if g.get('group_id') in blocked_groups or g['id'].split('-')[0] in blocked_groups];gate_ids={g['id'] for g in gates};active_ids={g.get('AA_target') for g in gates};blocked_ids=[o['id'] for o in objects if o.get('POLY_target') in gate_ids or o.get('AA_target') in active_ids]
questions=[dict(id='R1A',scope='G01/G02 upper long-MOS source correspondence, not previously adjudicated Q1',question='上方左侧长排MOS：栅CT实际从上端、下端还是双端引出？紫色旧G候选是否落在源漏列／环上？请在宽视野原图指出一处真实栅端（或确认蓝T候选带）。',reason='old source locators can select a bright diffusion column or guard; absent diffusion access near the same phase exposes this ambiguity',gate_groups=['G01','G02'],status='needs_human_terminal_source_anchor'),dict(id='R1B',scope='G05/G06 upper right long-MOS source correspondence',question='上方右侧长排MOS请同样确认栅CT引出侧与一处真实栅端；不能直接套用左侧或已审Q3方向。',gate_groups=['G05','G06'],status='needs_human_terminal_source_anchor'),dict(id='R2',scope='upper adjacent guards, independent of already confirmed Q3A inner top guard',question='AA图A为上方内环下边，B为紧邻外环上边。POLY图U处的亮带CT属于A、B，还是两环各有一排？看不清可保留未知；不把同一亮点归两环。',status='needs_human_guard_source_ownership')]
wr(B/'review-questions-v1.json',dict(questions=questions,previous_Q1_Q2_Q3_closed=True,not_individual_hole_count_review=True))
stage=dict(status='HOLD_new_source_correspondence_and_overall_acceptance',geometry_status='PASS',cleanup_of_8_old_recipes='all independently reinspected; wrong locators retired; physical unknowns explicitly retained',residual20='all have evidence-linked disposition, not all restored as cuts',full_frame_candidate='GENERATED',overall_human_acceptance=False,whole_frame_complete=False,working_candidate_frozen_for_review=True,blocking_human_cases=['R1A','R1B','R2'],source_review_required_for_groups=blocked_groups,source_review_required_for_contact_ids=blocked_ids,CT_count=len(objects),prior10025_exact_records_preserved=len(old)-len(retired)-len(corrected),retired_unaccepted_records=len(retired),source_only_corrections=len(corrected),new_candidate_contacts=len(added),all7044_previous_human_scope_geometry_preserved=True,physical_PDK_DRC=False)
wr(B/'stage-gate-v1.json',stage)
model.update(stage_status=stage['status'],whole_frame_complete=False,stage_gate_ref=ref(B/'stage-gate-v1.json'),source_review_required_for_contact_ids=blocked_ids)
report.update(geometry_status='PASS',stage_status=stage['status'],whole_frame_complete=False,source_correspondence_status='HOLD_R1A_R1B_R2',human_acceptance=False)
for key,val in [('model',model),('material-model',mat),('report',report),('ledger',rd(R/'ledger.json')),('terminal-access',access)]:wr(B/(key+'-v1.json'),val)
wr(B/'preservation-check-v1.json',dict(status='PASS',all_v2_material_records_exact_equal=True,all7044_records_exact_equal_to_v2=True,all7044_geometry_equal_to_original_approved_scope=True,all_unlisted_v2_contacts_exact_equal=True,retired_ids=sorted(retired),source_corrected_ids=sorted(corrected),new_ids=sorted(added),parent_inputs_and_v2_locked_JSON_hashes_valid=True,new_source_ownership=rd(B/'source-ownership-check-v1.json')))
shutil.copytree(R,A,dirs_exist_ok=True)
for key in ['model','material-model','report','terminal-access','stage-gate','source-reinspection','residual20-disposition','candidate-decisions','port-source-checks','preservation-check','review-questions']:
 shutil.copyfile(B/(key+'-v1.json'),A/(key+'.json'))
unknown=rd(B/'unknown-sites-v1.json')['unknown_scopes'];remaining=[x for x in access['diffusion_regions'] if not x['contact_ids']]
wr(B/'access-summary-v1.json',dict(reconstructed_diffusion_regions=access['diffusion_region_count'],candidate_direct_CT_access_regions=access['diffusion_region_count']-len(remaining),regions_without_direct_CT_evidence=remaining,no_direct_CT_does_not_imply_missing_cut=True,POLY_without_direct_CT=[x for x in access['POLY_materials'] if not x['contact_ids']],historical_fragment_exceptions=['V3_G1','V3_G2'],not_device_counts_or_accuracy=True))
shutil.copyfile(B/'access-summary-v1.json',A/'access-summary.json')
photo=Image.open('data/test_chip/tile_full/poly.jpg').convert('RGB');protected=set(oldby)-retired
extra=[dict(id='R1A',title='新增裁决：上方左侧长MOS栅端来源',source_bbox=[530,80,1830,380],layout_bbox=[800,390,2000,620],scope=questions[0]['question']),dict(id='R1B',title='新增裁决：上方右侧长MOS栅端来源',source_bbox=[2880,90,4090,390],layout_bbox=[2950,390,4020,600],scope=questions[1]['question']),dict(id='R2',title='新增裁决：上方近邻环CT归属',source_bbox=[650,620,1650,1070],layout_bbox=[900,750,1870,1290],scope=questions[2]['question'])]
extra_cards=[]
for c in extra:
 c['additional_modes']=[['inspection','png','原图候选标记（不是投影）']]
 if c['id']=='R2':c['additional_modes'].append(['aa','png','AA原图独立坐标参考'])
 extra_cards.append(render_case(c,mat,objects,protected,photo,A))
 bb=c['source_bbox'];im=photo.crop(bb);d=ImageDraw.Draw(im)
 if c['id'] in ['R1A','R1B']:
  ids=['G01-P05','G01-P06','G01-P07'] if c['id']=='R1A' else ['G05-P05','G05-P06','G05-P07','G06-P06']
  for o in objects:
   if o.get('POLY_target') not in ids:continue
   x,y=o['source_evidence']['native_center'];x-=bb[0];y-=bb[1]
   if 0<=x<im.width and 0<=y<im.height:d.ellipse((x-4,y-4,x+4,y+4),outline='#ed8eff',width=2);d.text((x+5,y-4),'old G?',fill='#ed8eff')
  # Structural candidate band, not a claim that every bright point is a gate CT.
  rect=[600,140,1500,172] if c['id']=='R1A' else [3010,171,3940,207]
  d.rectangle((rect[0]-bb[0],rect[1]-bb[1],rect[2]-bb[0],rect[3]-bb[1]),outline='#65baff',width=2);d.text((rect[0]-bb[0],rect[1]-bb[1]-14),'T: upper terminal candidate band',fill='#65baff')
 else:
  d.rectangle((1040-bb[0],807-bb[1],1340-bb[0],832-bb[1]),outline='#ffb45b',width=2);d.text((1040-bb[0],790-bb[1]),'U: bright band ownership unknown',fill='#ffb45b')
  aa_photo=Image.open('data/test_chip/tile_full/aa.jpg');ab=[700,850,1750,1300];ai=aa_photo.crop(ab);ad=ImageDraw.Draw(ai)
  for yy,lab,col in [(1015,'A: inner guard bottom','#65baff'),(1032,'B: outer guard top','#ffb45b')]:ad.line((350,yy-ab[1],900,yy-ab[1]),fill=col,width=2);ad.text((355,yy-ab[1]-13),lab,fill=col)
  ai.save(A/'R2-aa.png')
 im.save(A/(c['id']+'-inspection.png'))
cases=extra+s['cases'];wr(B/'review-windows-v1.json',dict(cases=cases,review_windows_are_not_separate_extraction_scopes=True))
ALLAA=unary_union([object_polygon(a) for a in mat['AA_objects']]);POLYS=[(g,Polygon(g['layout_outline'])) for g in mat['objects']];CTS=[(o,Polygon(o['layout_outline'])) for o in objects]
# Full-frame and per-window previews use one identical material/contact model.
for c in cases:
 key=c['id'];l,t,r,b=c['layout_bbox'];view=box(l,t,r,b);scale=min(3,(2400 if key=='O' else 1800)/(r-l));im=Image.new('RGB',(round((r-l)*scale),round((b-t)*scale)),'#111c28');d=ImageDraw.Draw(im)
 def pts(coords):return [((x-l)*scale,(y-t)*scale) for x,y in coords]
 geom=ALLAA.intersection(view);parts=list(geom.geoms) if hasattr(geom,'geoms') else [geom]
 for p in sorted([p for p in parts if p.geom_type=='Polygon'],key=lambda p:Polygon(p.exterior).area,reverse=True):
  if p.is_empty:continue
  d.polygon(pts(p.exterior.coords),fill='#315548',outline='#86b5a5')
  for h in p.interiors:d.polygon(pts(h.coords),fill='#111c28')
 for g,p in POLYS:
  if p.intersects(view):d.line(pts(p.exterior.coords),fill='#f7c85c',width=1 if key=='O' else 2)
 for o,p in CTS:
  if p.intersects(view):d.polygon(pts(p.exterior.coords),fill='#829ca6' if o['id'] in protected else '#ed8eff' if o.get('landing_material')=='POLY' else '#65baff')
 view_svg=svg(mat,c['layout_bbox']);glyphs=['<g data-layer="CT">']
 for o,p in CTS:
  if p.intersects(view):
   color='#829ca6' if o['id'] in protected else '#ed8eff' if o.get('landing_material')=='POLY' else '#65baff';points=' '.join(f'{x},{y}' for x,y in o['layout_outline']);glyphs.append(f'<polygon points="{points}" fill="{color}"><title>{o["id"]}</title></polygon>')
 glyphs.append('</g><g data-layer="unknown">')
 scopes=[(u['id'],u['layout_bounds']) for u in unknown]+[(o['id'],o['layout_bounds']) for o in remaining]
 for label,bounds in scopes:
  if box(*bounds).intersects(view):
   x1,y1,x2,y2=bounds;glyphs.append(f'<rect x="{x1}" y="{y1}" width="{x2-x1}" height="{y2-y1}" fill="none" stroke="#ffb45b" stroke-width="1.5" stroke-dasharray="5 3"><title>{label}: unknown, not a CT slot</title></rect>');d.rectangle(pts([(x1,y1),(x2,y2)]),outline='#ffb45b',width=2)
 if key=='R2':
  for yy,lab,col in [(1036.77555,'A','#65baff'),(1052.6597,'B','#ffb45b')]:glyphs.append(f'<text x="1410" y="{yy-3}" fill="{col}" font-size="12">{lab}</text>');d.text(pts([(1410,yy-5)])[0],lab,fill=col)
 glyphs.append('</g>');view_svg=view_svg.replace('</svg>',''.join(glyphs)+'</svg>');(A/(key+'-layout.svg')).write_text(view_svg);im.save(A/(key+'-preview.png'))
# Reuse original generated card markup and prepend new source questions only.
base_page=(R/'index.html').read_text();start=base_page.index('<section>');cards=''.join(extra_cards)+base_page[start:base_page.rindex('</html>')]
for c in cases:
 key=c['id'];needle=f'<option value="{key}-layout.svg">';idx=cards.index('</option>',cards.index(needle))+len('</option>');cards=cards[:idx]+f'<option value="{key}-preview.png">规则图PNG备用</option>'+cards[idx:]
# Question cards open on source context; answered old Q cards remain optional spot checks.
for key in ['R1A','R1B','R2']:cards=cards.replace(f'<img id="{key}" src="{key}-layout.svg"',f'<img id="{key}" src="{key}-inspection.png"')
paths=rd(B/'source-reinspection-v1.json')['paths'];path_rows=''.join('<tr><td>'+x['legacy'].removeprefix('BAND-')+'</td><td>'+x['status']+'</td><td>'+str(len(x['new_ids']))+'</td></tr>' for x in paths)
controls=''.join(f'<label><input type="checkbox" checked onchange="toggleLayer(\'{name}\',this.checked)">{name}</label> ' for name in ['AA','POLY','CT','unknown'])
whole=(A/'O-layout.svg').read_text();whole=whole.replace('<svg ','<svg id="whole-layout" ',1)
header=f'''<!doctype html><html lang="zh"><meta charset="utf-8"><title>CT全幅工作层：整体验收前来源门</title><style>body{{max-width:1500px;margin:24px auto;background:#111c28;color:#eee;font:17px sans-serif}}section{{border:1px solid #567;padding:16px;margin:20px 0}}img{{width:100%;max-height:90vh;object-fit:contain}}a{{color:#65baff}}select{{padding:10px}}table{{border-collapse:collapse;font-size:14px}}td,th{{border:1px solid #567;padding:8px}}#whole-layout{{width:100%;height:auto;max-height:95vh}}.hold{{border:2px solid #ffb45b}}</style><h1>CT全幅工作层：来源清理、端口证据、整体验收</h1><section class="hold"><h2>最终门暂不通过：请先处理新增R1A／R1B／R2</h2><p>旧Q1／Q2／Q3裁决保留，不重审。8条旧轨迹和20条零散候选已逐项调查处置；反例还牵出相邻未审轨迹，按整条撤回后重查。保留全部材料与原7044条批准范围；本轮新增234条候选、撤回33条未审CT、5条仅改来源，工作模型共10226条。</p><p><b>几何PASS不能替代真实来源。</b>上方G01/G02/G05/G06的旧栅CT取点可能落在源漏或环上；上部两条近邻环仍有共同亮带的归属歧义。这些范围已写入机器可读HOLD，禁止作为整层通过后直接追网。</p><p>端口盘点有846个重建扩散区域，其中839个有候选CT记录、7个暂无直接CT证据；内部节点可能不打孔，不能算7处漏检。两个V3材料是历史主体截段，保留旧端子关系。以上不是器件数、准确率或确认金属连接。</p><p>橙虚线是未知范围，不是待补孔。两块未定位小AA、上方两长AA条孔位可辨识度不足、上部近邻环及7个扩散区域保留未知；不能据此声称没有CT。</p><p><a href="#R1A">R1A左上长排栅端</a> · <a href="#R1B">R1B右上长排栅端</a> · <a href="#R2">R2近邻环归属</a> · <a href="#full">全幅分层视图</a> · <a href="review-questions.json">问题清单</a> · <a href="stage-gate.json">整层HOLD门</a> · <a href="terminal-access.json">端口证据表</a> · <a href="preservation-check.json">保护检查</a></p><pre>R1A：上端／下端／双端；真实栅端位置……
R1B：上端／下端／双端；真实栅端位置……
R2：A／B／各有一排／仍不清楚</pre></section><section id="full"><h2>同一全幅模型：可切换AA／POLY／CT／未知</h2><p>{controls}</p>{whole}<p><a href="O-preview.png">打开全幅PNG</a> · <a href="O-source.png">当前照片取点图</a> · <a href="../ct-full-frame-adjudication-v2/index.html">上一版已裁决基线</a></p></section><details><summary>8条旧轨迹调查结果（0不等于物理无孔；详细状态见机器记录）</summary><table><tr><th>旧路径</th><th>处置</th><th>新候选记录</th></tr>{path_rows}</table></details>'''
script='''<script>function toggleLayer(name,visible){document.querySelectorAll('#whole-layout [data-layer="'+name+'"]').forEach(el=>el.style.display=visible?'':'none')}</script>'''
(A/'index.html').write_text(header+cards+script+'</html>')
ui_labels={'independent_visible_left_edge_reinspection': '左侧可见范围重新定位，原错误亮点不复用', 'old_locator_retired_material_source_still_unknown': '撤回旧定位；小AA的孔位来源仍未知', 'wrong_cross_row_locator_retired_CT_observability_unknown': '撤回跨行旧定位；亮条上的孔位尚不能可靠区分', 'independent_row_relocalized_using_human_Q3B_reference': '按已审Q3B参考独立重取环行', 'independent_row_relocalized_using_human_Q3C_reference': '按已审Q3C参考独立重取环行', 'new_independent_interval_hypotheses_partial_recovery_central_assignment_unknown': '两侧独立重取，中段两环归属待R2裁决'}
ui_page=(A/'index.html').read_text()
for old_label,new_label in ui_labels.items():ui_page=ui_page.replace('<td>'+old_label+'</td>','<td>'+new_label+'</td>')
ui_page=ui_page.replace('>unknown</label>','>未知</label>')
for source_key in ['R1A','R1B','R2']:ui_page=ui_page.replace(f'<option value="{source_key}-inspection.png">',f'<option value="{source_key}-inspection.png" selected>')
(A/'index.html').write_text(ui_page)
# Freeze a review candidate; this is not the user's final physical approval.
wr(B/'freeze-manifest-v1.json',dict(state='FROZEN_REVIEW_CANDIDATE_NOT_ACCEPTED',whole_frame_complete=False,human_accepted=False,parent_ref=ref(P/'model-v1.json'),assets_index=ref(A/'index.html'),locked_files={p.name:sha(p) for p in B.glob('*.json') if p.name!='freeze-manifest-v1.json'},rebuild_command='.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-work-layer-closeout-v3/spec-v1.json --output runs/NEW_DIR',not_physical_PDK_DRC=True))
prov=B/'provenance';prov.mkdir(exist_ok=True)
for p in ['/tmp/prepare_ct_work_layer_v3.py','/tmp/package_ct_work_layer_v3.py']:shutil.copyfile(p,prov/Path(p).name)
(prov/'README.md').write_text('审计配方，非新增生产案例脚本或skill；基础执行复用ct_transfer。禁止原地覆盖已冻结版本；端口证据盘点不把内部扩散缺CT当失败，不按网格补孔。\n')
class Links(HTMLParser):
 def handle_starttag(self,t,a):
  a=dict(a)
  if a.get('id'):ids.append(a['id'])
  for k in ['src','href','value']:
   v=a.get(k,'')
   if v.endswith(('.json','.svg','.png','.html')):links.append(v)
ids=[];links=[];page=(A/'index.html').read_text();Links().feed(page);assert len(ids)==len(set(ids))
for target in re.findall(r'href="#([^"]+)"',page):assert target in ids,target
for link in links:assert (A/link).exists(),link
for p in A.glob('*.svg'):ET.parse(p)
for p in A.glob('*.png'):
 with Image.open(p) as im:im.verify()
print('PACKAGED',len(objects),'contacts;',len(links),'local resources; source gate HOLD; full-frame layers and all review cards generated')
