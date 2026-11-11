import sys, math
sys.path.insert(0, '/home/tj/CompressorController/Hardware/audit')
from parse_board import parse, find_all, get

PCB = '/home/tj/CompressorController/Hardware/CompressorController.kicad_pcb'
b = parse(open(PCB).read())

# board outline
rect = find_all(b, 'gr_rect')[0]
x1 = float(get(rect, 'start')[1]); y1 = float(get(rect, 'start')[2])
x2 = float(get(rect, 'end')[1]);   y2 = float(get(rect, 'end')[2])
print('outline', x1, y1, x2, y2)

W = 2400
scale = W / (x2 - x1)
H = int((y2 - y1) * scale)
def px(x): return (x - x1) * scale
def py(y): return (y - y1) * scale

out = []
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
out.append('<rect width="100%" height="100%" fill="#101418"/>')
out.append(f'<rect x="{px(x1)}" y="{py(y1)}" width="{px(x2)-px(x1)}" height="{py(y2)-py(y1)}" fill="#1b2129" stroke="#888" stroke-width="2"/>')

def rot(px_, py_, ang):
    a = math.radians(ang)
    return (px_*math.cos(a) - py_*math.sin(a), px_*math.sin(a) + py_*math.cos(a))

# pads
for fp in find_all(b, 'footprint'):
    fat = get(fp, 'at')
    fx, fy = float(fat[1]), float(fat[2])
    frot = float(fat[3]) if len(fat) > 3 else 0.0
    for p in fp:
        if not (isinstance(p, list) and p and p[0] == 'pad'):
            continue
        net = get(p, 'net'); nm = net[1] if net else ''
        pat = get(p, 'at')
        dx, dy = rot(float(pat[1]), float(pat[2]), frot)
        cx, cy = fx + dx, fy + dy
        sz = get(p, 'size'); w, h = float(sz[1]), float(sz[2])
        prot = float(pat[3]) if len(pat) > 3 else 0.0
        color = '#555'
        if nm == 'GND': color = '#37d67a'
        elif nm == '+3V3': color = '#ff4d4d'
        elif nm in ('+15V', '+5V'): color = '#ffb020'
        out.append(f'<g transform="translate({px(cx):.2f},{py(cy):.2f}) rotate({prot})">'
                   f'<rect x="{-w*scale/2:.2f}" y="{-h*scale/2:.2f}" width="{w*scale:.2f}" height="{h*scale:.2f}" '
                   f'fill="{color}" opacity="0.75"/></g>')

# vias
for v in find_all(b, 'via'):
    net = get(v, 'net'); nm = net[1] if net else ''
    at = get(v, 'at'); vx, vy = float(at[1]), float(at[2])
    sz = get(v, 'size'); r = float(sz[1]) / 2 * scale
    color = '#888'
    if nm == 'GND': color = '#00ff88'
    elif nm == '+3V3': color = '#ff2222'
    elif nm == 'Net-(D14-A)': color = '#2255ff'
    elif nm == '+15V': color = '#ffaa00'
    elif nm == '+5V': color = '#00dddd'
    out.append(f'<circle cx="{px(vx):.2f}" cy="{py(vy):.2f}" r="{max(r,2.5):.2f}" fill="none" stroke="{color}" stroke-width="1.6"/>')

# refs
for fp in find_all(b, 'footprint'):
    ref = None
    for p in fp:
        if isinstance(p, list) and p and p[0] == 'property' and len(p) > 2 and p[1] == 'Reference':
            ref = p[2]
    fat = get(fp, 'at'); fx, fy = float(fat[1]), float(fat[2])
    out.append(f'<text x="{px(fx):.1f}" y="{py(fy):.1f}" fill="#c8d0da" font-size="11" font-family="monospace" text-anchor="middle">{ref}</text>')

out.append('</svg>')
open('/home/tj/CompressorController/Hardware/audit/board.svg', 'w').write('\n'.join(out))
print('wrote board.svg', W, H)
