"""Place GND / +3V3 net vias on CompressorController, matching the user's existing style.

Rules derived from the board file and the examples already placed:
  * via 0.6 mm / drill 0.3 mm, through F.Cu..B.Cu
  * GND pad vias sit ~0.55 mm outside the pad edge, inside the GND pour
    (no track needed: the F.Cu pour ties them to the pad)
  * +3V3 pad vias sit next to the pad inside the In1 +3V3 pour and are
    joined to the pad with a 0.2 mm F.Cu stub
  * clearance: Default 0.2 mm, HV class nets 2.0 mm
  * copper to board edge 0.5 mm, hole-to-hole 0.25 mm
"""
import sys, math, json, uuid
sys.path.insert(0, '/home/tj/CompressorController/Hardware/audit')
from parse_board import parse, find_all, get

PCB = '/home/tj/CompressorController/Hardware/CompressorController.kicad_pcb'
b = parse(open(PCB).read())

VIA_R = 0.3
VIA_DRILL_R = 0.15
HV = {
    '/PFC/AC_sense', '/PFC/DC_Bus_In_+', '/Phases/DC Bus +',
    '/Phases/U Power out', '/Phases/V Power out', '/Phases/W Power out',
    '/Power in/AC L', '/Power in/AC N',
    'Net-(C38-Pad1)', 'Net-(C38-Pad2)', 'Net-(C42-Pad1)', 'Net-(C43-Pad2)',
    'Net-(D14-A)', 'Net-(PS1-AC(L))',
}
CLR_DEFAULT = 0.2
CLR_HV = 2.0
EDGE_CLR = 0.5
HOLE_CLR = 0.25

def clr(net):
    return CLR_HV if net in HV else CLR_DEFAULT

def clr_between(a, c):
    return max(CLR_DEFAULT, clr(a), clr(c))

def _isnum(v):
    try:
        float(v); return True
    except Exception:
        return False

# ---------------------------------------------------------------- geometry
def rot(p, q, a):
    r = math.radians(a)
    return (p * math.cos(r) - q * math.sin(r), p * math.sin(r) + q * math.cos(r))

def point_rect_dist(px, py, cx, cy, w, h, ang):
    """Distance from point to a rotated rectangle (0 inside)."""
    dx, dy = px - cx, py - cy
    r = math.radians(-ang)
    lx = dx * math.cos(r) - dy * math.sin(r)
    ly = dx * math.sin(r) + dy * math.cos(r)
    ex = max(abs(lx) - w / 2, 0.0)
    ey = max(abs(ly) - h / 2, 0.0)
    return math.hypot(ex, ey)

def point_seg_dist(px, py, x1, y1, x2, y2):
    vx, vy = x2 - x1, y2 - y1
    wx, wy = px - x1, py - y1
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / L2))
    return math.hypot(px - (x1 + t * vx), py - (y1 + t * vy))

def seg_rect_dist(x1, y1, x2, y2, cx, cy, w, h, ang):
    """Approximate distance between a segment and a rotated rectangle."""
    # sample the segment; rectangles are small relative to the sampling step
    n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 0.15) + 1)
    best = 1e9
    for i in range(n + 1):
        t = i / n
        px, py = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
        best = min(best, point_rect_dist(px, py, cx, cy, w, h, ang))
        if best == 0:
            return 0.0
    return best

# ---------------------------------------------------------------- board data
# board outline
rect = find_all(b, 'gr_rect')[0]
BX1 = float(get(rect, 'start')[1]); BY1 = float(get(rect, 'start')[2])
BX2 = float(get(rect, 'end')[1]);   BY2 = float(get(rect, 'end')[2])

# zones
zones = []
for z in find_all(b, 'zone'):
    net = get(z, 'net'); lay = get(z, 'layer'); lays = get(z, 'layers')
    ko = get(z, 'keepout')
    pts = [x for x in get(z, 'polygon') if isinstance(x, list) and x[0] == 'pts'][0]
    poly = [(float(c[1]), float(c[2])) for c in pts if isinstance(c, list) and c[0] == 'xy']
    zones.append(dict(net=(net[1] if net else None),
                      layers=([lay[1]] if lay else (lays[1:] if lays else [])),
                      keepout=ko is not None,
                      vias_allowed=not (ko and any(isinstance(k, list) and k and k[0] == 'vias' and k[1] == 'not_allowed' for k in ko)),
                      poly=poly))
KEEPOUTS = [z for z in zones if z['keepout'] and not z['vias_allowed']]
GND_ZONE = [z for z in zones if z['net'] == 'GND' and not z['keepout']][0]
P3V3_ZONE = [z for z in zones if z['net'] == '+3V3' and not z['keepout']][0]

def fills_for(net, layer):
    out = []
    for z in find_all(b, 'zone'):
        if get(z, 'keepout'):
            continue
        n = get(z, 'net')
        if not n or n[1] != net:
            continue
        for f in [c for c in z if isinstance(c, list) and c and c[0] == 'filled_polygon']:
            l = get(f, 'layer')
            if not l or l[1] != layer:
                continue
            pts = [x for x in f if isinstance(x, list) and x[0] == 'pts'][0]
            out.append([(float(c[1]), float(c[2])) for c in pts if isinstance(c, list) and c[0] == 'xy'])
    return out

GND_PLANE_FILLS = fills_for('GND', 'In2.Cu')
P3V3_PLANE_FILLS = fills_for('+3V3', 'In1.Cu')

def in_poly(px, py, poly):
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > py) != (y2 > py):
            if px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
                c = not c
    return c

# pads
pads = []
for fp in find_all(b, 'footprint'):
    ref = val = None
    for p in fp:
        if isinstance(p, list) and p and p[0] == 'property' and len(p) > 2:
            if p[1] == 'Reference': ref = p[2]
            if p[1] == 'Value': val = p[2]
    fat = get(fp, 'at'); fx, fy = float(fat[1]), float(fat[2])
    fr = float(fat[3]) if len(fat) > 3 else 0.0
    for p in fp:
        if not (isinstance(p, list) and p and p[0] == 'pad'):
            continue
        net = get(p, 'net'); nm = net[1] if net else ''
        pat = get(p, 'at')
        # KiCad stores the footprint angle for a Y-down board; pad offsets must
        # be rotated with the opposite sign (verified against pcbnew/DRC geometry).
        dx, dy = rot(float(pat[1]), float(pat[2]), -fr)
        sz = get(p, 'size'); w, h = float(sz[1]), float(sz[2])
        ang = float(pat[3]) if len(pat) > 3 else 0.0
        drill = get(p, 'drill')
        dr = 0.0
        if drill:
            vals = [float(v) for v in drill[1:] if not isinstance(v, list) and _isnum(v)]
            if vals: dr = max(vals)
        lays = get(p, 'layers')[1:]
        copper = [l for l in lays if l.endswith('.Cu')]
        allcu = any(l.startswith('*.') for l in lays)
        pads.append(dict(ref=ref, num=p[1], net=nm, x=fx + dx, y=fy + dy,
                         w=w, h=h, ang=ang, type=p[2], drill=dr,
                         copper=('ALL' if allcu else copper)))

# traces
traces = []
for s in find_all(b, 'segment'):
    net = get(s, 'net'); st = get(s, 'start'); en = get(s, 'end')
    traces.append(dict(net=net[1] if net else '', x1=float(st[1]), y1=float(st[2]),
                       x2=float(en[1]), y2=float(en[2]), w=float(get(s, 'width')[1]),
                       layer=get(s, 'layer')[1]))

# vias
vias = []
for v in find_all(b, 'via'):
    net = get(v, 'net'); at = get(v, 'at'); sz = get(v, 'size'); dr = get(v, 'drill')
    lays = get(v, 'layers')
    vias.append(dict(net=net[1] if net else '', x=float(at[1]), y=float(at[2]),
                     size=float(sz[1]), drill=float(dr[1]),
                     layers=(lays[1:] if lays else []),
                     free=(get(v, 'free')[1] if get(v, 'free') else 'no')))

# ---------------------------------------------------------------- spatial index
CELL = 2.0
GRID = {}

def _cells(x1, y1, x2, y2):
    for gx in range(int(math.floor(x1 / CELL)), int(math.floor(x2 / CELL)) + 1):
        for gy in range(int(math.floor(y1 / CELL)), int(math.floor(y2 / CELL)) + 1):
            yield (gx, gy)

def add_obstacle(idx):
    ob = OBSTACLES[idx]
    pad = 2.2  # max clearance we ever need
    hw = ob.get('hw', 0.0); hh = ob.get('hh', 0.0)
    r = ob.get('r', 0.0)
    if ob['kind'] in ('pad', 'trace'):
        if ob['kind'] == 'pad':
            r = math.hypot(hw, hh)
        else:
            r = ob.get('r', 0.0)
        x1, x2 = min(ob['x1'], ob['x2']) - r - pad, max(ob['x1'], ob['x2']) + r + pad
        y1, y2 = min(ob['y1'], ob['y2']) - r - pad, max(ob['y1'], ob['y2']) + r + pad
    else:
        x1, x2 = ob['x'] - r - pad, ob['x'] + r + pad
        y1, y2 = ob['y'] - r - pad, ob['y'] + r + pad
    for c in _cells(x1, y1, x2, y2):
        GRID.setdefault(c, []).append(idx)

OBSTACLES = []
for p in pads:
    OBSTACLES.append(dict(kind='pad', net=p['net'], x=p['x'], y=p['y'],
                          x1=p['x'], y1=p['y'], x2=p['x'], y2=p['y'],
                          w=p['w'], h=p['h'], hw=p['w'] / 2, hh=p['h'] / 2,
                          ang=p['ang'], drill=p['drill'],
                          copper=p['copper'], ref=p['ref'], num=p['num']))
for t in traces:
    OBSTACLES.append(dict(kind='trace', net=t['net'], x1=t['x1'], y1=t['y1'],
                          x2=t['x2'], y2=t['y2'], r=t['w'] / 2, w=t['w'],
                          layer=t['layer'], copper=[t['layer']]))
for v in vias:
    OBSTACLES.append(dict(kind='via', net=v['net'], x=v['x'], y=v['y'], r=v['size'] / 2,
                          drill=v['drill'], copper='ALL'))
for i in range(len(OBSTACLES)):
    OBSTACLES[i]['idx'] = i
    OBSTACLES[i]['hw'] = OBSTACLES[i].get('hw', 0.0)
    OBSTACLES[i]['hh'] = OBSTACLES[i].get('hh', 0.0)
    add_obstacle(i)

def near(px, py):
    seen = set()
    for c in _cells(px - 2.2, py - 2.2, px + 2.2, py + 2.2):
        for i in GRID.get(c, ()):
            if i not in seen:
                seen.add(i); yield OBSTACLES[i]

# ---------------------------------------------------------------- checks
def edge_ok(x, y, extra=0.0):
    return (x - BX1 >= VIA_R + EDGE_CLR + extra and
            BX2 - x >= VIA_R + EDGE_CLR + extra and
            y - BY1 >= VIA_R + EDGE_CLR + extra and
            BY2 - y >= VIA_R + EDGE_CLR + extra)

def in_keepout(x, y):
    return any(in_poly(x, y, k['poly']) for k in KEEPOUTS)

def in_plane(net, x, y):
    """True when (x,y) is over the copper of the plane that terminates `net`."""
    if net == 'GND':
        return any(in_poly(x, y, p) for p in GND_PLANE_FILLS)
    if net == '+3V3':
        return any(in_poly(x, y, p) for p in P3V3_PLANE_FILLS)
    return True

def via_clear(x, y, net, ignore=(), clearance_scale=1.0, same_net_pad_gap=0.0,
              min_via_dist=1.2, extra=0.0):
    """True when a 0.6/0.3 via at (x,y) on `net` respects every rule.

    same_net_pad_gap: minimum copper gap to a same-net pad (0 = touching is fine).
    """
    if not edge_ok(x, y):
        return False
    if in_keepout(x, y):
        return False
    for ob in near(x, y):
        if ob['idx'] in ignore:
            continue
        # only copper matters; ignore footprints with no copper
        if ob['net'] == net:
            # same net: copper may touch, but drills must stay 0.25 mm apart
            if ob['kind'] == 'via' and math.hypot(x - ob['x'], y - ob['y']) < min_via_dist:
                return False
            if ob.get('drill'):
                need = VIA_DRILL_R + ob['drill'] / 2 + HOLE_CLR
                if ob['kind'] == 'via':
                    if math.hypot(x - ob['x'], y - ob['y']) < need:
                        return False
            if same_net_pad_gap > 0 and ob['kind'] == 'pad':
                if point_rect_dist(x, y, ob['x'], ob['y'], ob['w'], ob['h'], ob['ang']) < VIA_R + same_net_pad_gap:
                    return False
            continue
        req = clr_between(net, ob['net']) * clearance_scale + extra
        if ob['kind'] == 'pad':
            d = point_rect_dist(x, y, ob['x'], ob['y'], ob['w'], ob['h'], ob['ang'])
            if d < VIA_R + req: return False
            if ob['drill']:
                if d < VIA_DRILL_R + ob['drill'] / 2 + HOLE_CLR: return False
        elif ob['kind'] == 'trace':
            d = point_seg_dist(x, y, ob['x1'], ob['y1'], ob['x2'], ob['y2'])
            if d < VIA_R + ob['r'] + req: return False
        else:
            d = math.hypot(x - ob['x'], y - ob['y'])
            if d < VIA_R + ob['r'] + req: return False
            if d < min_via_dist: return False
            if ob.get('drill') and d < VIA_DRILL_R + ob['drill'] / 2 + HOLE_CLR:
                return False
    return True

def stub_clear(x1, y1, x2, y2, net, width, ignore=()):
    """Clear a 0.2 mm stub capsule against other-net copper."""
    for ob in near((x1 + x2) / 2, (y1 + y2) / 2):
        pass
    # query a bounding box of the stub
    xs = [x1, x2]; ys = [y1, y2]
    seen = set()
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    rr = math.hypot(x2 - x1, y2 - y1) / 2 + 2.2
    for c in _cells(cx - rr, cy - rr, cx + rr, cy + rr):
        for i in GRID.get(c, ()):
            if i in seen: continue
            seen.add(i)
            ob = OBSTACLES[i]
            if ob['idx'] in ignore or ob['net'] == net:
                continue
            req = clr_between(net, ob['net'])
            if ob['kind'] == 'pad':
                d = seg_rect_dist(x1, y1, x2, y2, ob['x'], ob['y'], ob['w'], ob['h'], ob['ang'])
                if d < VIA_R * 0 + width / 2 + req: return False
            elif ob['kind'] == 'trace':
                d = min(point_seg_dist(x1, y1, ob['x1'], ob['y1'], ob['x2'], ob['y2']),
                        point_seg_dist(x2, y2, ob['x1'], ob['y1'], ob['x2'], ob['y2']),
                        point_seg_dist(ob['x1'], ob['y1'], x1, y1, x2, y2),
                        point_seg_dist(ob['x2'], ob['y2'], x1, y1, x2, y2))
                if d < width / 2 + ob['r'] + req: return False
            else:
                d = min(point_seg_dist(ob['x'], ob['y'], x1, y1, x2, y2), 0)
                if point_seg_dist(ob['x'], ob['y'], x1, y1, x2, y2) < width / 2 + ob['r'] + req:
                    return False
    return True

# ---------------------------------------------------------------- report helpers
def nearest_via(net, x, y):
    best = None
    for v in vias:
        if v['net'] != net: continue
        d = math.hypot(v['x'] - x, v['y'] - y)
        if best is None or d < best[0]: best = (d, v)
    return best

if __name__ == '__main__':
    print('board', BX1, BY1, BX2, BY2)
    print('pads', len(pads), 'traces', len(traces), 'vias', len(vias))
    print('keepouts', len(KEEPOUTS), [k['layers'] for k in KEEPOUTS])
    print('GND zone poly', len(GND_ZONE['poly']), 'layers', GND_ZONE['layers'])
    print('3V3 zone poly', len(P3V3_ZONE['poly']), 'layers', P3V3_ZONE['layers'])
