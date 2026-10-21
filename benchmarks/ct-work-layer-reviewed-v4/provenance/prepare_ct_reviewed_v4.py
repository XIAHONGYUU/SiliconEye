"""Audit recipe: apply the 2026-10-21 R1/R2 review with locked generic ct_transfer inputs.
Run from the repository with .venv Python; raw photos and frozen parents are read-only.
"""
from pathlib import Path
import copy
import hashlib
import json
from collections import Counter

import cv2
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

from silicon_eye.ct_joint_reconstruction import audit_contacts
from silicon_eye.geometry_reconstruction import object_polygon

B = Path('benchmarks/ct-work-layer-reviewed-v4')
P = Path('benchmarks/ct-work-layer-closeout-v3')
def rd(p): return json.loads(Path(p).read_text())
def wr(p, x): Path(p).write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p): return dict(path=str(p), sha256=sha(p))
assert not (B/'freeze-manifest-v1.json').exists(), 'Never overwrite a frozen package'
parent = rd(P/'model-v1.json')['objects']
materials = rd(P/'material-model-v1.json')
mat = copy.deepcopy(materials)
budget = rd(P/'spec-v1.json')['budget']
polys = {o['id']: o for o in mat['objects']}
active = {o['id']: o for o in mat['AA_objects']}
groups = ['G01', 'G02', 'G05', 'G06']
gate_ids = {g['id'] for g in mat['objects'] if g.get('group_id') in groups}
aa_ids = {polys[k]['AA_target'] for k in gate_ids}
retired = [o for o in parent if o.get('POLY_target') in gate_ids or o.get('AA_target') in aa_ids]
approved = {o['id'] for o in rd('benchmarks/ct-lower-middle-mos-revision-v2/model-v1.json')['objects']}
assert not approved.intersection(o['id'] for o in retired)
changes = [dict(id=o['id'], before=o, after=None,
                reason='R1 upper-only source reinspection replaces the entire unaccepted source recipe; old top labels are not trusted optical identities') for o in retired]

# R2: two AI material identities described the same continuous rail. Keep A's ID and
# all of its reviewed CT geometry; absorb B explicitly with an alias and full source history.
A = 'AA2-UPPER-INNER-B-AA-0'
C = 'AA2-UPPER-COMPLEX-GUARD-AA-0-split01'
a, c = active[A], active[C]
rail_low = min(y for h in a['holes_xy'] for x,y in h if y > 1000)
rail_high = max(y for x,y in a['outer_xy'])
row_y = (rail_low + rail_high) / 2
cb = object_polygon(c).bounds
old_low = min(y for x,y in c['outer_xy'])
old_high = sorted(set(y for x,y in c['outer_xy']))[1]
new_c = copy.deepcopy(c)
new_c['outer_xy'] = [[x, rail_low if y == old_low else rail_high if y == old_high else y] for x,y in c['outer_xy']]
merged = unary_union([object_polygon(a), object_polygon(new_c)])
assert merged.geom_type == 'Polygon' and merged.is_valid
after_a = copy.deepcopy(a)
after_a.update(outer_xy=[list(v) for v in merged.exterior.coords[:-1]],
               holes_xy=[[list(v) for v in h.coords[:-1]] for h in merged.interiors],
               outer_xyxy=list(merged.bounds), hole_xyxy=None,
               material_aliases=[C], source_state='human_confirmed_R2_continuity_one_CT_row',
               source_geometry_scope='original A observation retained; B observation archived in merge history',
               merged_source_records=[copy.deepcopy(a), copy.deepcopy(c)],
               local_review=dict(case='R2', human_review=ref(B/'human-review-v1.json'),
                                 exact_new_boundary='AI_orthogonal_candidate_from_confirmed_continuity',
                                 electrical_scope='continuous_AA_only_no_new_M1_or_net_claim'))
material_changes = {'objects': [], 'AA_objects': [dict(id=A, before=a, after=after_a), dict(id=C, before=c, after=None)]}
mat['AA_objects'] = [after_a if o['id'] == A else o for o in mat['AA_objects'] if o['id'] != C]
active = {o['id']: o for o in mat['AA_objects']}
central = sorted([o for o in parent if o['family'] == 'UP-RING-BOTTOM'], key=lambda o:o['layout_center'][0])
phase = central[0]['layout_center'][0]
pitch = central[1]['layout_center'][0] - phase
assert abs(pitch-13) < 1e-6 and abs(central[0]['layout_center'][1]-row_y) < 1e-6
for o in parent:
    if o.get('AA_target') != C: continue
    q = copy.deepcopy(o)
    q['AA_target'] = A
    q['material_identity_history'] = [dict(before=C, after=A, reason='human R2 continuous AA; old ID retained as alias', human_review=ref(B/'human-review-v1.json'))]
    if o['family'] in ['COMPLEX-LEFT','COMPLEX-RIGHT']:
        slot = int(round((o['layout_center'][0]-phase)/pitch))
        x = phase + slot*pitch
        q.update(layout_center=[x,row_y], layout_outline=[[x-2.5,row_y-2.5],[x+2.5,row_y-2.5],[x+2.5,row_y+2.5],[x-2.5,row_y+2.5]],
                 family='R2-SHARED-RAIL-EXTENSION', column=slot, row=0)
    changes.append(dict(id=o['id'],before=o,after=q,reason='R2 named AA merge; source unchanged; only unaccepted side-rail candidates moved onto the single shared row'))

change_by = {x['id']:x for x in changes}
working = [change_by[o['id']]['after'] if o['id'] in change_by else o for o in parent]
working = [o for o in working if o is not None]
gray = cv2.imread('data/test_chip/tile_full/poly.jpg',0)
smooth = cv2.GaussianBlur(gray,(5,5),1).astype(float)
residual = smooth-cv2.GaussianBlur(smooth,(0,0),4)
poly_union = unary_union([Polygon(g['layout_outline']) for g in mat['objects']])
AA_union = unary_union([object_polygon(o) for o in mat['AA_objects']])
base_shapes = [Polygon(o['layout_outline']) for o in working]
base_tree = STRtree(base_shapes)
source_tree = cKDTree([o['source_evidence']['native_center'] for o in working])
additions, observations, rejected, fits = [], [], [], []

def peak(key, bb):
    l,t,r,b = map(int, bb)
    patch = residual[t:b,l:r]
    dy,dx = np.unravel_index(patch.argmax(),patch.shape)
    x,y = int(l+dx),int(t+dy)
    ev = dict(native_center=[x,y],source_native_center_xy=[x,y],source_observation_id=key,
              peak_gray=float(smooth[y,x]),local_residual=float(residual[y,x]),source_roi=[l,t,r,b],
              supported=bool(smooth[y,x]>=205 and residual[y,x]>=20),algorithm_detected=True,
              evidence_type='bounded_raw_peak_with_human_terminal_side_and_AI_ordered_material_correspondence')
    observations.append(dict(id=key,source_evidence=ev))
    return ev

# The R1 cap check exposes a competing H3 recipe drifting across those caps. Reinspect
# the complete named recipe on the distinct guard band instead of letting the old
# first-exported assignment suppress a correctly localized gate CT.
source_corrections = []
for o in working:
    if o.get('AA_target') != 'AA2-TOP-H3-AA-0': continue
    assert o['id'] not in approved
    nx = int(round(o['source_evidence']['native_center'][0]))
    prediction = int(110 + .0095*nx)
    lo,hi = prediction-12,prediction+13
    ridge = smooth[lo:hi,nx-25:nx+26].mean(axis=1)
    ny = lo + int(ridge.argmax())
    ev = peak('V4-H3-SOURCE-'+o['id'],[nx-4,ny-3,nx+5,ny+4])
    ev['evidence_type'] = 'independent_guard_band_ridge_and_bounded_peak_after_gate_counterexample'
    assert ev['supported']
    source_corrections.append(dict(id=o['id'],before_source_evidence=copy.deepcopy(o['source_evidence']),
                                   after_source_evidence=ev,reason='The entire unaccepted H3 locator drifted onto confirmed R1 upper gate caps; remeasure the distinct upper guard band, preserving design geometry and original evidence in history'))
    o['source_evidence'] = ev
source_tree = cKDTree([o['source_evidence']['native_center'] for o in working])

def add(key, target, xy, ev, kind, family, col, row):
    x,y = map(float,xy)
    o = dict(id=key, family=family,column=col,row=row,layer='CT',landing_material=kind,
             **{('AA_target' if kind=='AA' else 'POLY_target'):target},layout_center=[x,y],
             layout_outline=[[x-2.5,y-2.5],[x+2.5,y-2.5],[x+2.5,y+2.5],[x-2.5,y+2.5]],
             source_frame='poly',source_evidence=ev,status='human_side_confirmed_AI_local_geometry_candidate',
             M1_enclosure='unknown',net_id=None)
    shape = Polygon(o['layout_outline'])
    host = object_polygon(active[target]) if kind=='AA' else Polygon(polys[target]['layout_outline'])
    other = poly_union if kind=='AA' else AA_union
    reason = None
    if not ev['supported']: reason='no_independent_observed_peak'
    elif not host.buffer(-1).covers(shape) or shape.distance(other)<1-1e-8: reason='material_enclosure_or_channel_clearance'
    elif any(shape.distance(base_shapes[i])<3-1e-8 for i in base_tree.query(shape.buffer(3))): reason='preserved_CT_gap_conflict'
    elif any(shape.distance(Polygon(q['layout_outline']))<3-1e-8 for q in additions): reason='new_CT_gap_conflict'
    elif source_tree.query_ball_point(ev['native_center'],3): reason='prior_optical_point_already_owned'
    elif any(np.linalg.norm(np.array(q['source_evidence']['native_center'])-ev['native_center'])<=3 for q in additions): reason='new_optical_point_already_owned'
    if reason: rejected.append(dict(candidate=o,reason=reason));return
    additions.append(o)

# Wide-field cap observations, ordered independently of the old material native bboxes.
# The rightmost block has four visible caps versus five old material records; do not
# manufacture a fifth cap or silently retire a previously reviewed POLY identity.
cap_centers = {
 'G01':[638,683,734,795,842,893,953,1001,1069,1117,1171,1231,1281,1331,1395,1444],
 'G02':[1582,1626,1689,1742],
 'G05':[3068,3114,3171,3223,3289,3336,3385],
 'G06':[3441,3488,3534,3591,3641],
}
for group, centers in cap_centers.items():
    gs = sorted([g for g in mat['objects'] if g.get('group_id')==group],key=lambda g:g['id'])[:len(centers)]
    for g,nx in zip(gs,centers,strict=True):
        ylo,yhi = ((140,173) if group=='G01' else (148,178) if group=='G02' else (170,207))
        # Two distinct bounded optical cores in the confirmed short terminal bar.
        local = smooth[ylo:yhi,nx-18:nx+19].mean(axis=0)
        weights = np.maximum(local-np.percentile(local,25),0)
        cx = float(np.dot(np.arange(nx-18,nx+19),weights)/weights.sum())
        bounds = Polygon(g['layout_outline']).bounds
        gx = (bounds[0]+bounds[2])/2
        for col, (l,r,dx) in enumerate([(int(cx-16),int(cx),-6),(int(cx+1),int(cx+18),6)]):
            key = 'CTV4-GATE-'+g['id']+'-'+str(col)
            ev = peak(key,[l,ylo,r,yhi])
            add(key,g['id'],[gx+dx,bounds[1]+4],ev,'POLY','V4-GATE-'+g['id'],col,0)
        fits.append(dict(id=g['id'],source_band=[nx-20,ylo,nx+21,yhi],ordered_cap_locator=nx,local_bar_center=cx,
                         confirmed_side='upper_only',material_geometry_unchanged=True))

# Diffusion CT is measured only on independently identified body columns. Five rows
# are observed here; a rejected optical window stays unknown rather than a synthetic cut.
sd = [
 ('AA-F01755',[607,661,714,766,816,873,924,975,1044,1098,1152,1204,1259,1312,1365,1419,1474],191,15.5),
 ('AA-F01757',[1552,1605,1661,1711,1764],196,15.5),
 ('AA-F01803',[3040,3092,3144,3193,3259,3310,3363,3412,3461,3513,3564,3613,3665],212,15.5),
]
for target, seeds, first_y, source_pitch in sd:
    gates = sorted([g for g in mat['objects'] if g.get('AA_target')==target], key=lambda g:Polygon(g['layout_outline']).centroid.x)
    remain = object_polygon(active[target]).difference(unary_union([Polygon(g['layout_outline']) for g in gates]))
    windows = sorted(list(remain.geoms),key=lambda p:p.centroid.x)
    assert len(windows)==len(seeds),target
    ay1,ay2 = object_polygon(active[target]).bounds[1::2]
    row_origin = ay1+12
    row_pitch = (ay2-ay1-24)/4
    for col, (window,nx) in enumerate(zip(windows,seeds,strict=True)):
        family = 'V4-SD-'+target+('-INTERIOR' if 0<col<len(seeds)-1 else '-EDGE'+str(col))
        for row in range(5):
            ny=first_y+source_pitch*row+(nx-seeds[0])*.005
            ev=peak(f'CTV4-SD-{target}-{col}-{row}',[nx-6,int(ny-6),nx+7,int(ny+7)])
            add(f'CTV4-SD-{target}-{col}-{row}',target,[window.centroid.x,row_origin+row*row_pitch],ev,'AA',family,col,row)
    fits.append(dict(id=target,source_columns=seeds,source_first_row=first_y,source_pitch=source_pitch,
                     canonical_row_origin=row_origin,canonical_row_pitch=row_pitch,observed_row_count=5,
                     interior_column_pitch='derived_from_unchanged_regular_POLY_windows',edge_columns='separate limited-width diffusion windows'))

unknown = rd(P/'unknown-sites-v1.json')
unknown['unknown_scopes']=[u for u in unknown['unknown_scopes'] if u.get('id')!='U-COMPLEX-CENTRE']
unknown['unknown_scopes'].append(dict(id='U-R1B-RIGHT-COUNT',kind='POLY_count_source_correspondence_conflict',AA_target='AA-F01804',
                                    POLY_ids=['G06-P06','G06-P07','G06-P08','G06-P09','G06-P10'],
                                    layout_bounds=[3743,425,3958,550],source_bbox=[3670,140,4000,350],
                                    visible_upper_caps=[3771,3816,3871,3922],old_material_count=5,observed_caps=4,
                                    status='retain_material_history_do_not_invent_fifth_terminal',question_for_human='右上末段是否为四条栅，而非旧模型五条？'))
final=working+additions
audit=audit_contacts(final,mat,budget)
wr(B/'preflight-geometry-v1.json',audit)
wr(B/'optical-observations-v1.json',dict(objects=observations,nonexported=rejected,fits=fits))
wr(B/'material-merge-v1.json',dict(case='R2',surviving_id=A,retired_id=C,shared_row_y=row_y,
                                shared_row_pitch=pitch,source_records_retained=True,
                                AA_continuity_human_confirmed=True,new_M1_or_net_identity=False))
if audit['status']!='PASS':
    print(json.dumps(audit,ensure_ascii=False)[:6000]);raise SystemExit(1)
points=np.array([o['source_evidence']['native_center'] for o in final])
new_ids={o['id'] for o in additions}
conflicts=[]
for i,j in cKDTree(points).query_pairs(3):
    x,y=final[i],final[j]
    if not ({x['id'],y['id']} & new_ids): continue
    if x.get('AA_target',x.get('POLY_target'))!=y.get('AA_target',y.get('POLY_target')):conflicts.append([x['id'],y['id']])
assert not conflicts,conflicts
review=rd(B/'human-review-v1.json')
authorization=dict(human_review_ref=ref(B/'human-review-v1.json'),
                   authorized_material_ids=[A,C],authorized_contact_ids=[o['id'] for o in changes],
                   authorized_new_contact_ids=sorted(new_ids),authorized_source_correspondence_ids=[c['id'] for c in source_corrections],
                   scope='apply named R1/R2 decisions; new exact coordinates remain AI candidates, no whole-frame acceptance')
wr(B/'authorization-v1.json',authorization)
wr(B/'new-contacts-v1.json',dict(objects=additions))
wr(B/'unknown-sites-v1.json',unknown)
wr(B/'source-ownership-check-v1.json',dict(status='PASS_for_new_points',radius_px=3,conflicts=conflicts))
wr(B/'review-questions-v1.json',dict(closed_cases=['R1A','R1B','R2'],new_questions=[dict(id='R1B-COUNT',question=unknown['unknown_scopes'][-1]['question_for_human'],reason='four optical cap groups and five diffusion columns versus old five POLY gates; do not fit CT to an extra gate')]))
spec=dict(operation='apply_local_review_revision',audit_terminal_access=True,
          inputs=dict(materials=ref(P/'material-model-v1.json'),contacts=ref(P/'model-v1.json'),parent_spec=ref(P/'spec-v1.json'),
                      photo=ref('data/test_chip/tile_full/poly.jpg'),AA_photo=ref('data/test_chip/tile_full/aa.jpg'),
                      human_review=ref(B/'authorization-v1.json'),adjudication=ref(B/'human-review-v1.json'),
                      new_contacts=ref(B/'new-contacts-v1.json'),unknown_sites=ref(B/'unknown-sites-v1.json'),observations=ref(B/'optical-observations-v1.json')),
          budget=budget,material_changes=material_changes,contact_changes=changes,source_correspondence_corrections=source_corrections,review_images=[],
          review_title='CT局部裁决落地：上端栅CT与连续AA单排孔',
          review_notes='R1A/R1B上端引出、R2连续AA单排CT已确认；旧Q1/Q2/Q3和无关已审结果不重跑。右上末段出现旧POLY五条与原图四个栅端的数量冲突，单列阻塞，不补虚构CT。',
          cases=[dict(id=c['id'],title=c['title'],source_bbox=c['source_bbox'],layout_bbox=c['layout_bbox'],scope='局部修订，原图观察和规则几何是独立坐标，不是投影。') for c in rd(P/'review-windows-v1.json')['cases'] if c['id'] in ['R1A','R1B','R2','O']])
wr(B/'spec-v1.json',spec)
print(json.dumps(dict(total=len(final),retired=len(retired),retargeted=sum(x['after'] is not None for x in changes),new=len(additions),AA=len(mat['AA_objects']),POLY=len(mat['objects']),rejected=Counter(x['reason'] for x in rejected),geometry=audit['status']),ensure_ascii=False))
