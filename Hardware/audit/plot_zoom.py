import sys, math
sys.path.insert(0, '/home/tj/CompressorController/Hardware/audit')
from parse_board import parse, find_all, get

PCB = '/home/tj/CompressorController/Hardware/CompressorController.kicad_pcb'
b = parse(open(PCB).read())

x1, y1, x2, y2 = (float(v) for v in sys.argv[1:5])
ppm = float(sys.argv[5]) if len(sys.argv) > 5 else 60.0
OUT = sys.argv[6] if len(sys.argv) > 6 else '/home/tj/CompressorController/Hardware/audit/zoom.svg'

W = int((x2 - x1) * ppm); H = int((y2 - y1) * ppm)
def px(x): return (x - x1) * ppm
def py(y): return (y - y1) * ppm

def rot(p, q, a):
    r = math.radians(a)
    return (p*math.cos(r) - q*math.sin(r), p*math.sin(r) + q*math.cos(r))

out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       '<rect width="100%" height="100%" fill="#0d1117"/>']

NETC = {'GND': '#37d67a', '+3V3': '#ff4d4d', '+15V': '#ffb020', '+5V': '#ffe066'}

# traces
for s in find_all(b, 'segment'):
    net = get(s, 'net'); nm = net[1] if net else ''
    st = get(s, 'start'); en = get(s, 'end'); lay = get(s, 'layer')[1]
    c = NETC.get(nm, '#4a5568')
    op = 0.9 if nm in NETC else 0.45
    out.append(f'<line x1="{px(float(st[1])):.2f}" y1="{py(float(st[2])):.2f}" x2="{px(float(en[1])):.2f}" y2="{py(float(en[2])):.2f}" stroke="{c}" stroke-width="{max(1.0,float(get(s,"width")[1])*ppm*0.6):.1f}" opacity="{op}" stroke-linecap="round"/>')

# pads
for fp in find_all(b, 'footprint'):
    ref = None
    for p in fp:
        if isinstance(p, list) and p and p[0] == 'property' and len(p) > 2 and p[1] == 'Reference':
            ref = p[2]
    fat = get(fp, 'at'); fx, fy = float(fat[1]), float(fat[2])
    fr = float(fat[3]) if len(fat) > 3 else 0.0
    for p in fp:
        if not (isinstance(p, list) and p and p[0] == 'pad'):
            continue
        net = get(p, 'net'); nm = net[1] if net else ''
        pat = get(p, 'at'); dx, dy = rot(float(pat[1]), float(pat[2]), fr)
        cx, cy = fx + dx, fy + dy
        sz = get(p, 'size'); w, h = float(sz[1]), float(sz[2])
        prot = float(pat[3]) if len(pat) > 3 else 0.0
        c = NETC.get(nm, '#8899aa')
        out.append(f'<g transform="translate({px(cx):.2f},{py(cy):.2f}) rotate({prot})">'
                   f'<rect x="{-w*ppm/2:.2f}" y="{-h*ppm/2:.2f}" width="{w*ppm:.2f}" height="{h*ppm:.2f}" rx="{min(w,h)*ppm*0.2:.2f}" '
                   f'fill="{c}" opacity="0.85"/></g>')
        out.append(f'<text x="{px(cx):.1f}" y="{py(cy)-h*ppm/2-2:.1f}" fill="#e6edf3" font-size="9" font-family="monospace" text-anchor="middle">{ref}.{p[1]}</text>')

# vias
for v in find_all(b, 'via'):
    net = get(v, 'net'); nm = net[1] if net else ''
    at = get(v, 'at'); vx, vy = float(at[1]), float(at[2])
    sz = get(v, 'size'); r = float(sz[1]) / 2 * ppm
    dr = get(v, 'drill'); rd = float(dr[1]) / 2 * ppm
    c = NETC.get(nm, '#aaaaaa')
    out.append(f'<circle cx="{px(vx):.2f}" cy="{py(vy):.2f}" r="{max(r,3):.2f}" fill="{c}" fill-opacity="0.35" stroke="{c}" stroke-width="2"/>')
    out.append(f'<circle cx="{px(vx):.2f}" cy="{py(vy):.2f}" r="{max(rd,1.2):.2f}" fill="#0d1117"/>')

out.append('</svg>')
open(OUT, 'w').write('\n'.join(out))
print('wrote', OUT, W, H)
