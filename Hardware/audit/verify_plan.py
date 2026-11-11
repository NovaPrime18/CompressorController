"""Independent brute-force verification of the via plan (no spatial index, no shared code paths)."""
import sys, math, json
sys.path.insert(0, '/home/tj/CompressorController/Hardware/audit')
from via_engine import (pads, traces, vias, BX1, BY1, BX2, BY2, KEEPOUTS,
                        GND_ZONE, P3V3_ZONE, HV, in_poly, in_plane, point_rect_dist,
                        point_seg_dist, VIA_R, VIA_DRILL_R, EDGE_CLR, HOLE_CLR)

plan = json.load(open('/home/tj/CompressorController/Hardware/audit/via_plan.json'))
NEW = plan['vias']; NEWSEG = plan['segs']

def clr(net): return 2.0 if net in HV else 0.2

problems = []

# 1. via-vs-via (existing + new)
allv = [(v['net'], v['x'], v['y'], v['drill'], v['size']) for v in vias] + \
       [(v['net'], v['x'], v['y'], 0.3, 0.6) for v in NEW]
for i in range(len(vias), len(allv)):
    net, x, y, dr, sz = allv[i]
    for j in range(len(allv)):
        if i == j:
            continue
        n2, x2, y2, d2, s2 = allv[j]
        d = math.hypot(x - x2, y - y2)
        need = (sz / 2) + (s2 / 2) + max(clr(net), clr(n2)) + 0.15 if n2 != net else VIA_DRILL_R + d2 / 2 + HOLE_CLR
        if n2 != net:
            need = max(need, VIA_DRILL_R + d2 / 2 + HOLE_CLR)
        need = max(need, 1.4)
        if d < need - 1e-6:
            problems.append(('via-via', net, round(x, 2), round(y, 2), n2, round(d, 3), round(need, 3)))

# 2. via-vs-pad
for i in range(len(vias), len(allv)):
    net, x, y, dr, _sz = allv[i]
    for p in pads:
        d = point_rect_dist(x, y, p['x'], p['y'], p['w'], p['h'], p['ang'])
        if p['net'] == net:
            if d < VIA_R + 0.04 and not p['drill']:
                problems.append(('via-in-pad', net, round(x, 2), round(y, 2), p['ref'] + '.' + p['num'], round(d, 3)))
            if p['drill']:
                hole_d = math.hypot(x - p['x'], y - p['y'])
                if hole_d < VIA_DRILL_R + p['drill'] / 2 + HOLE_CLR - 1e-6:
                    problems.append(('via-pad hole', net, round(x, 2), round(y, 2), p['ref'] + '.' + p['num'], round(hole_d, 3)))
        else:
            need = VIA_R + max(clr(net), clr(p['net'])) + 0.15
            if d < need - 1e-6:
                problems.append(('via-pad clearance', net, round(x, 2), round(y, 2), p['ref'] + '.' + p['num'] + '/' + p['net'], round(d, 3), round(need, 3)))
            if p['drill']:
                hole_d = math.hypot(x - p['x'], y - p['y'])
                if hole_d < VIA_DRILL_R + p['drill'] / 2 + HOLE_CLR - 1e-6:
                    problems.append(('via-pad hole', net, round(x, 2), round(y, 2), p['ref'] + '.' + p['num'], round(hole_d, 3)))

# 3. via-vs-trace
for i in range(len(vias), len(allv)):
    net, x, y, dr, _sz = allv[i]
    for t in traces:
        d = point_seg_dist(x, y, t['x1'], t['y1'], t['x2'], t['y2'])
        if t['net'] == net:
            continue
        need = VIA_R + t['w'] / 2 + max(clr(net), clr(t['net'])) + 0.15
        if d < need - 1e-6:
            problems.append(('via-trace', net, round(x, 2), round(y, 2), t['net'] + ' w' + str(t['w']), round(d, 3), round(need, 3)))

# 4. edge / keepout / pour containment
for v in NEW:
    x, y, net = v['x'], v['y'], v['net']
    if min(x - BX1, BX2 - x, y - BY1, BY2 - y) < VIA_R + EDGE_CLR - 1e-6:
        problems.append(('edge', net, round(x, 2), round(y, 2)))
    if any(in_poly(x, y, k['poly']) for k in KEEPOUTS):
        problems.append(('keepout', net, round(x, 2), round(y, 2)))
    if not in_plane(net, x, y):
        problems.append(('not over plane', net, round(x, 2), round(y, 2)))

# 5. stubs: connected to a pad, clear of other nets
for s in NEWSEG:
    ok_pad = any(math.hypot(s['x1'] - p['x'], s['y1'] - p['y']) < 0.45 or
                 math.hypot(s['x2'] - p['x'], s['y2'] - p['y']) < 0.45 for p in pads)
    ok_via = any(math.hypot(s['x1'] - v['x'], s['y1'] - v['y']) < 0.3 or
                 math.hypot(s['x2'] - v['x'], s['y2'] - v['y']) < 0.3 for v in NEW)
    if not (ok_pad or ok_via):
        problems.append(('stub floating', s['net'], round(s['x1'], 2), round(s['y1'], 2)))
    for p in pads:
        if p['net'] == s['net']:
            continue
        d = min(point_rect_dist(s['x1'], s['y1'], p['x'], p['y'], p['w'], p['h'], p['ang']),
                point_rect_dist(s['x2'], s['y2'], p['x'], p['y'], p['w'], p['h'], p['ang']))
        need = s['w'] / 2 + max(clr(s['net']), clr(p['net']))
        if d < need - 1e-6:
            problems.append(('stub-pad', s['net'], round(s['x1'], 2), round(s['y1'], 2), p['ref'] + '.' + p['num'], round(d, 3), round(need, 3)))
    for t in traces:
        if t['net'] == s['net']:
            continue
        d = min(point_seg_dist(t['x1'], t['y1'], s['x1'], s['y1'], s['x2'], s['y2']),
                point_seg_dist(t['x2'], t['y2'], s['x1'], s['y1'], s['x2'], s['y2']))
        need = s['w'] / 2 + t['w'] / 2 + max(clr(s['net']), clr(t['net']))
        if d < need - 1e-6:
            problems.append(('stub-trace', s['net'], round(s['x1'], 2), round(s['y1'], 2), t['net'], round(d, 3), round(need, 3)))

print('new vias', len(NEW), 'new stubs', len(NEWSEG))
print('problems', len(problems))
for pr in problems[:60]:
    print('  ', pr)
from collections import Counter
print(Counter(p[0] for p in problems))
