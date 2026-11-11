import sys, math
sys.path.insert(0, '/home/tj/CompressorController/Hardware/audit')
from parse_board import parse, find_all, get
from collections import defaultdict

PCB = '/home/tj/CompressorController/Hardware/CompressorController.kicad_pcb'
b = parse(open(PCB).read())

def rot(px_, py_, ang):
    a = math.radians(ang)
    return (px_*math.cos(a) - py_*math.sin(a), px_*math.sin(a) + py_*math.cos(a))

# pads: (ref, padnum, net, x, y, w, h, layer_type)
pads = []
for fp in find_all(b, 'footprint'):
    ref = None
    for p in fp:
        if isinstance(p, list) and p and p[0] == 'property' and len(p) > 2 and p[1] == 'Reference':
            ref = p[2]
    fat = get(fp, 'at'); fx, fy = float(fat[1]), float(fat[2])
    frot = float(fat[3]) if len(fat) > 3 else 0.0
    for p in fp:
        if not (isinstance(p, list) and p and p[0] == 'pad'):
            continue
        net = get(p, 'net'); nm = net[1] if net else ''
        pat = get(p, 'at')
        dx, dy = rot(float(pat[1]), float(pat[2]), frot)
        sz = get(p, 'size')
        pads.append(dict(ref=ref, num=p[1], net=nm, x=fx+dx, y=fy+dy,
                         w=float(sz[1]), h=float(sz[2]), type=p[2],
                         layers=[l for l in get(p, 'layers')[1:] if l.endswith('.Cu')]))

vias = []
for v in find_all(b, 'via'):
    net = get(v, 'net'); at = get(v, 'at'); sz = get(v, 'size'); dr = get(v, 'drill')
    layers = get(v, 'layers'); free = get(v, 'free')
    vias.append(dict(net=net[1] if net else '', x=float(at[1]), y=float(at[2]),
                     size=float(sz[1]), drill=float(dr[1]),
                     layers=layers[1:], free=(free[1] if free else 'no')))

segs = []
for s in find_all(b, 'segment'):
    net = get(s, 'net'); st = get(s, 'start'); en = get(s, 'end')
    segs.append(dict(net=net[1] if net else '', x1=float(st[1]), y1=float(st[2]),
                     x2=float(en[1]), y2=float(en[2]),
                     w=float(get(s, 'width')[1]), layer=get(s, 'layer')[1]))

def d(a, bx, by): return math.hypot(a[0]-bx, a[1]-by)

print('pads', len(pads), 'vias', len(vias), 'segs', len(segs))

for target in ('+3V3', 'GND'):
    pv = [v for v in vias if v['net'] == target]
    pp = [p for p in pads if p['net'] == target]
    print(f'\n===== {target}: {len(pv)} vias, {len(pp)} pads =====')
    # trace connections for each via
    for v in sorted(pv, key=lambda v: (v['y'], v['x'])):
        touching = [s for s in segs if s['net'] == target and (d((s['x1'],s['y1']), v['x'], v['y']) < 0.02 or d((s['x2'],s['y2']), v['x'], v['y']) < 0.02)]
        other_ends = []
        for s in touching:
            for (ex, ey) in ((s['x1'],s['y1']), (s['x2'],s['y2'])):
                if d((ex,ey), v['x'], v['y']) > 0.02:
                    other_ends.append((round(ex,3), round(ey,3), s['layer']))
        nearpads = sorted(((d((p['x'],p['y']), v['x'], v['y']), p['ref'], p['num'], p['type']) for p in pp))[:3]
        print(f" via ({v['x']:.2f},{v['y']:.2f}) free={v['free']} segs={len(touching)} ends={other_ends}")
        print('      nearest pads:', [(round(a,2), b_, c, e) for a,b_,c,e in nearpads])
