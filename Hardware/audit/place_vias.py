import sys, math, json, uuid
sys.path.insert(0, '/home/tj/CompressorController/Hardware/audit')
from via_engine import *  # noqa

STITCH_PITCH = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
GND_GAP = 0.55
P3_GAP = 0.45

new_vias = []      # dict(x,y,net,free,kind,ref,num)
new_segs = []      # dict(x1,y1,x2,y2,net,w,layer)
skipped = []       # (ref,num,reason)

def commit_via(v):
    new_vias.append(v)
    idx = len(OBSTACLES)
    OBSTACLES.append(dict(kind='via', net=v['net'], x=v['x'], y=v['y'], r=VIA_R,
                          drill=0.3, copper='ALL', idx=idx, hw=0.0, hh=0.0))
    add_obstacle(idx)

def commit_seg(sg):
    new_segs.append(sg)
    if sg['net'] == '+3V3':
        _p3_segs.append((sg['x1'], sg['y1'], sg['x2'], sg['y2']))
    idx = len(OBSTACLES)
    OBSTACLES.append(dict(kind='trace', net=sg['net'], x1=sg['x1'], y1=sg['y1'],
                          x2=sg['x2'], y2=sg['y2'], r=sg['w'] / 2, w=sg['w'],
                          layer=sg['layer'], copper=[sg['layer']], idx=idx,
                          hw=0.0, hh=0.0))
    add_obstacle(idx)

def pad_extent(p, ux, uy):
    """Half-extent of a rotated rectangle along unit vector, and the point on that face."""
    a = math.radians(p['ang'])
    # dot of rotated local axes with the direction
    ex = (p['w'] / 2) * abs(math.cos(a) * ux + math.sin(a) * uy)
    ey = (p['h'] / 2) * abs(-math.sin(a) * ux + math.cos(a) * uy)
    return ex + ey

def rect_dist_pad(p, x, y, ignore_self=True):
    return point_rect_dist(x, y, p['x'], p['y'], p['w'], p['h'], p['ang'])

def gnd_via_exists(p, radius=0.95):
    for v in vias + new_vias:
        if v['net'] != 'GND':
            continue
        if rect_dist_pad(p, v['x'], v['y']) <= radius:
            return True
    return False

# +3V3 connectivity: walk the +3V3 trace graph from a pad and see whether it reaches a via
_p3_nodes = []
for t in traces:
    if t['net'] == '+3V3':
        _p3_nodes.append((t['x1'], t['y1']))
        _p3_nodes.append((t['x2'], t['y2']))
_p3_segs = [(t['x1'], t['y1'], t['x2'], t['y2']) for t in traces if t['net'] == '+3V3']

def p3v3_via_exists(p, radius=0.9):
    """True when a +3V3 trace leaves this pad and reaches a +3V3 via."""
    seeds = []
    for (x1, y1, x2, y2) in _p3_segs:
        if math.hypot(x1 - p['x'], y1 - p['y']) < 0.45: seeds.append((x1, y1))
        if math.hypot(x2 - p['x'], y2 - p['y']) < 0.45: seeds.append((x2, y2))
    if not seeds:
        return False
    # flood the trace graph
    seen = set(seeds)
    stack = list(seeds)
    while stack:
        x, y = stack.pop()
        for v in vias + new_vias:
            if v['net'] == '+3V3' and math.hypot(x - v['x'], y - v['y']) < 0.35:
                return True
        for (x1, y1, x2, y2) in _p3_segs:
            for (ex, ey, ox, oy) in ((x1, y1, x2, y2), (x2, y2, x1, y1)):
                if math.hypot(ex - x, ey - y) < 0.02 and (ox, oy) not in seen:
                    seen.add((ox, oy)); stack.append((ox, oy))
    return False

# ------------------------------------------------------------------ +3V3
p3_pads = [p for p in pads if p['net'] == '+3V3']
p3_over_plane = [p for p in p3_pads if in_plane('+3V3', p['x'], p['y'])]
print(f'+3V3 pads {len(p3_pads)}, over +3V3 pour {len(p3_over_plane)}')

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]

def make_stub(p, x, y, net):
    """Return a clear 0.2 mm L-shaped stub (pad centre -> via), or None."""
    variants = []
    if abs(x - p['x']) > 1e-6:
        variants.append([(p['x'], p['y'], x, p['y']), (x, p['y'], x, y)])
    if abs(y - p['y']) > 1e-6:
        variants.append([(p['x'], p['y'], p['x'], y), (p['x'], y, x, y)])
    if not variants:
        variants.append([])
    for segs in variants:
        segs = [sg for sg in segs if math.hypot(sg[2] - sg[0], sg[3] - sg[1]) > 1e-6]
        if all(stub_clear(a_, b_, c, d_, net, 0.2) for a_, b_, c, d_ in segs):
            return segs
    return None
for p in p3_over_plane:
    if p3v3_via_exists(p):
        # already tied to a via by the existing stub
        continue
    best = None
    for gap in (P3_GAP, 0.65, 0.85, 1.1, 1.4, 1.8, 2.4, 3.0):
        for dx, dy in DIRS:
            L = math.hypot(dx, dy)
            ux, uy = dx / L, dy / L
            ext = pad_extent(p, ux, uy)
            for lat in (0.0, 0.3, -0.3, 0.6, -0.6, 1.0, -1.0, 1.5, -1.5):
                # lateral shift perpendicular to the direction
                px_ = ux * (ext + gap) - uy * lat
                py_ = uy * (ext + gap) + ux * lat
                x, y = p['x'] + px_, p['y'] + py_
                if not in_plane('+3V3', x, y):
                    continue
                if not via_clear(x, y, '+3V3', same_net_pad_gap=0.05, extra=0.3, min_via_dist=1.4):
                    continue
                segs = make_stub(p, x, y, '+3V3')
                if segs is None:
                    continue
                d = math.hypot(x - p['x'], y - p['y'])
                if best is None or d < best[0]:
                    best = (d, x, y, segs)
        if best:
            break
    if best is None:
        skipped.append((p['ref'], p['num'], '+3V3 no room'))
        continue
    d, x, y, segs = best
    commit_via(dict(x=x, y=y, net='+3V3', free='no', kind='p3', ref=p['ref'], num=p['num']))
    for a, b_, c, d2 in segs:
        commit_seg(dict(x1=a, y1=b_, x2=c, y2=d2, net='+3V3', w=0.2, layer='F.Cu'))

for p in p3_over_plane:
    if p3v3_via_exists(p):
        continue
    best = None
    for r in [i / 20.0 for i in range(12, 121)]:
        for k in range(0, 72):
            a = math.radians(k * 5)
            x = p['x'] + r * math.cos(a)
            y = p['y'] + r * math.sin(a)
            if not in_plane('+3V3', x, y):
                continue
            if not via_clear(x, y, '+3V3', same_net_pad_gap=0.05, extra=0.3, min_via_dist=1.4):
                continue
            segs = make_stub(p, x, y, '+3V3')
            if segs is None:
                continue
            best = (r, x, y, segs)
            break
        if best:
            break
    if best:
        r, x, y, segs = best
        commit_via(dict(x=x, y=y, net='+3V3', free='no', kind='p3', ref=p['ref'], num=p['num']))
        for a_, b_, c, d_ in segs:
            commit_seg(dict(x1=a_, y1=b_, x2=c, y2=d_, net='+3V3', w=0.2, layer='F.Cu'))
        print(f'  fallback +3V3 via for {p["ref"]}.{p["num"]} at {r:.2f} mm')
    else:
        skipped.append((p['ref'], p['num'], '+3V3 no room (fallback)'))

print('+3V3 vias new', sum(1 for v in new_vias if v['net'] == '+3V3'),
      'stubs', len(new_segs))

# ------------------------------------------------------------------ GND pad vias
gnd_pads = [p for p in pads if p['net'] == 'GND']
print('GND pads', len(gnd_pads))
placed_pad_vias = 0
for p in gnd_pads:
    if gnd_via_exists(p):
        continue
    if not in_poly(p['x'], p['y'], GND_ZONE['poly']):
        skipped.append((p['ref'], p['num'], 'GND pad outside GND pour'))
        continue
    got = 0
    used = []
    for gap in (GND_GAP, 0.75, 0.95, 1.2):
        for dx, dy in DIRS:
            if got >= 2:
                break
            L = math.hypot(dx, dy)
            ux, uy = dx / L, dy / L
            ext = pad_extent(p, ux, uy)
            for lat in (0.0, 0.25, -0.25, 0.5, -0.5):
                x = p['x'] + ux * (ext + gap) - uy * lat
                y = p['y'] + uy * (ext + gap) + ux * lat
                if not in_plane('GND', x, y):
                    continue
                if any(math.hypot(x - a, y - b_) < 1.2 for a, b_ in used):
                    continue
                if not via_clear(x, y, 'GND', same_net_pad_gap=0.05, extra=0.3, min_via_dist=1.4):
                    continue
                commit_via(dict(x=x, y=y, net='GND', free='yes', kind='gnd_pad',
                                ref=p['ref'], num=p['num']))
                used.append((x, y))
                got += 1
                break
        if got >= 2:
            break
    if not got:
        skipped.append((p['ref'], p['num'], 'GND pad: no free side'))
    placed_pad_vias += got

# ---- fallback: pads with no free side get a dense radial search
def dense_search(p, net, need_stub, max_r=3.5):
    best = None
    import math as _m
    for r in [i / 20.0 for i in range(12, int(max_r * 20) + 1)]:
        for k in range(0, 72):
            a = _m.radians(k * 5)
            x = p['x'] + r * _m.cos(a)
            y = p['y'] + r * _m.sin(a)
            if net == '+3V3':
                if not in_plane('+3V3', x, y):
                    continue
            else:
                if not in_plane('GND', x, y):
                    continue
            if not via_clear(x, y, net, same_net_pad_gap=0.05, extra=0.3, min_via_dist=1.4):
                continue
            if need_stub:
                segs = []
                if abs(x - p['x']) > 1e-6:
                    segs.append((p['x'], p['y'], x, p['y']))
                if abs(y - p['y']) > 1e-6:
                    segs.append((x, p['y'], x, y))
                if not all(stub_clear(a_, b_, c, d_, net, 0.2) for a_, b_, c, d_ in segs):
                    continue
                best = (r, x, y, segs)
            else:
                best = (r, x, y, [])
            break
        if best:
            break
    return best

for p in gnd_pads:
    if not in_poly(p['x'], p['y'], GND_ZONE['poly']):
        continue
    if gnd_via_exists(p):
        continue
    # was it served by the pad-edge pass?
    if any(v['kind'] == 'gnd_pad' and v['ref'] == p['ref'] and v['num'] == p['num'] for v in new_vias):
        continue
    found = dense_search(p, 'GND', False)
    if found:
        r, x, y, segs = found
        for a_, b_, c, d_ in segs:
            commit_seg(dict(x1=a_, y1=b_, x2=c, y2=d_, net='GND', w=0.2, layer='F.Cu'))
        commit_via(dict(x=x, y=y, net='GND', free='yes', kind='gnd_pad', ref=p['ref'], num=p['num']))
        placed_pad_vias += 1
        print(f'  fallback GND via for {p["ref"]}.{p["num"]} at {r:.2f} mm')

print('GND pad vias new', placed_pad_vias)

# ------------------------------------------------------------------ GND stitching
def hex_points(x1, y1, x2, y2, pitch):
    dy = pitch * math.sqrt(3) / 2
    row = 0
    y = y1
    while y <= y2:
        x = x1 + (pitch / 2 if row % 2 else 0)
        while x <= x2:
            yield x, y
            x += pitch
        y += dy
        row += 1

def nearest_any_via(x, y):
    best = 1e9
    for v in vias + new_vias:
        d = math.hypot(v['x'] - x, v['y'] - y)
        if d < best:
            best = d
    return best

st = 0
tried = 0
for x, y in hex_points(BX1 + 1.0, BY1 + 1.0, BX2 - 1.0, BY2 - 1.0, STITCH_PITCH):
    tried += 1
    if not in_plane('GND', x, y):
        continue
    if nearest_any_via(x, y) < 1.6:
        continue
    if not via_clear(x, y, 'GND', same_net_pad_gap=0.3, extra=0.3, min_via_dist=1.4):
        continue
    commit_via(dict(x=x, y=y, net='GND', free='yes', kind='gnd_stitch', ref='', num=''))
    st += 1

print(f'GND stitching vias new {st} (grid candidates {tried}, pitch {STITCH_PITCH} mm)')
print('TOTAL new vias', len(new_vias), ' new stubs', len(new_segs))
print('skipped', len(skipped))
from collections import Counter
print(Counter(v['kind'] for v in new_vias))
for s in skipped[:40]:
    print('  skip', s)

# ---- sliver guard: a GND via whose 0.2 mm clearance hole passes close to a
# power-plane boundary leaves a copper sliver < 0.2 mm, which DRC flags as
# "connection too narrow".  Drop those vias.
PLANE_FILLS = [p_ for p_ in fills_for('+15V', 'In1.Cu')] + [p_ for p_ in fills_for('+3V3', 'In1.Cu')]

def gap_to_planes(cx, cy, clearance=0.5):
    best = 1e9
    for poly in PLANE_FILLS:
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
            d = point_seg_dist(cx, cy, x1, y1, x2, y2)
            if d < best:
                best = d
    return best - clearance

_drop = set()
for v in []:  # guard disabled
    if v['net'] != 'GND':
        continue
    g = gap_to_planes(v['x'], v['y'])
    if 0.0 <= g < 0.28:
        _drop.add(id(v))
if _drop:
    keep_vias = [v for v in new_vias if id(v) not in _drop]
    drop_xy = {(round(v['x'], 4), round(v['y'], 4)) for v in new_vias if id(v) in _drop}
    new_vias[:] = keep_vias
    new_segs[:] = [s_ for s_ in new_segs
                   if not ((round(s_['x2'], 4), round(s_['y2'], 4)) in drop_xy)]
    print(f'  sliver guard removed {len(_drop)} GND vias near power-plane edges')

# drop skip notes for pads that were ultimately served
_have = {(v['ref'], v['num']) for v in new_vias if v['kind'] == 'p3'}
skipped = [s_ for s_ in skipped if not (s_[0], s_[1]) in _have]

json.dump(dict(vias=new_vias, segs=new_segs, skipped=skipped,
               pitch=STITCH_PITCH), open('/home/tj/CompressorController/Hardware/audit/via_plan.json', 'w'), indent=1)
print('wrote audit/via_plan.json')
