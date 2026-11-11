import sys, math, json
sys.path.insert(0, '/home/tj/CompressorController/Hardware/audit')
from via_engine import *  # noqa

plan = json.load(open('/home/tj/CompressorController/Hardware/audit/via_plan.json'))
x1, y1, x2, y2 = (float(v) for v in sys.argv[1:5])
ppm = float(sys.argv[5])
OUT = sys.argv[6]
W, H = int((x2 - x1) * ppm), int((y2 - y1) * ppm)
def px(x): return (x - x1) * ppm
def py(y): return (y - y1) * ppm

out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       '<rect width="100%" height="100%" fill="#0b0f14"/>']

# board edge
out.append(f'<rect x="{px(BX1):.1f}" y="{py(BY1):.1f}" width="{px(BX2)-px(BX1):.1f}" height="{py(BY2)-py(BY1):.1f}" fill="#141a22" stroke="#667" stroke-width="1.5"/>')

# copper traces (thin grey), pads (net tinted)
NETC = {'GND': '#2e7d55', '+3V3': '#8a3030', '+15V': '#7a5a1e', '+5V': '#7a7a20'}
for t in traces:
    c = NETC.get(t['net'], '#2b3440')
    out.append(f'<line x1="{px(t["x1"]):.1f}" y1="{py(t["y1"]):.1f}" x2="{px(t["x2"]):.1f}" y2="{py(t["y2"]):.1f}" stroke="{c}" stroke-width="{max(0.8,t["w"]*ppm):.1f}" stroke-linecap="round" opacity="0.85"/>')
for p in pads:
    c = NETC.get(p['net'], '#46525f')
    out.append(f'<g transform="translate({px(p["x"]):.2f},{py(p["y"]):.2f}) rotate({p["ang"]})"><rect x="{-p["w"]*ppm/2:.2f}" y="{-p["h"]*ppm/2:.2f}" width="{p["w"]*ppm:.2f}" height="{p["h"]*ppm:.2f}" fill="{c}" opacity="0.9"/></g>')

# keepouts
for k in KEEPOUTS:
    pts = ' '.join(f'{px(a):.1f},{py(b_):.1f}' for a, b_ in k['poly'])
    out.append(f'<polygon points="{pts}" fill="#552222" opacity="0.35" stroke="#a44" stroke-width="1"/>')

# existing vias
for v in vias:
    c = '#7fd1ff' if v['net'] == 'GND' else ('#ff9f7f' if v['net'] == '+3V3' else '#5b6673')
    out.append(f'<circle cx="{px(v["x"]):.1f}" cy="{py(v["y"]):.1f}" r="{max(0.3*ppm,1.2):.1f}" fill="{c}" opacity="0.55"/>')

# new stubs
for s in plan['segs']:
    out.append(f'<line x1="{px(s["x1"]):.1f}" y1="{py(s["y1"]):.1f}" x2="{px(s["x2"]):.1f}" y2="{py(s["y2"]):.1f}" stroke="#ffdd55" stroke-width="{max(0.2*ppm,1.0):.1f}" stroke-linecap="round"/>')

# new vias
COL = {'gnd_pad': '#00e676', 'gnd_stitch': '#00b0ff', 'p3': '#ff3d00'}
for v in plan['vias']:
    c = COL.get(v['kind'], '#fff')
    r = max(0.3 * ppm, 1.4)
    out.append(f'<circle cx="{px(v["x"]):.1f}" cy="{py(v["y"]):.1f}" r="{r:.1f}" fill="none" stroke="{c}" stroke-width="1.4"/>')
    out.append(f'<circle cx="{px(v["x"]):.1f}" cy="{py(v["y"]):.1f}" r="{max(0.15*ppm,0.6):.1f}" fill="{c}"/>')

# refs
for fp_ref in set(p['ref'] for p in pads if p['ref']):
    pp = [p for p in pads if p['ref'] == fp_ref]
    cx = sum(p['x'] for p in pp) / len(pp); cy = sum(p['y'] for p in pp) / len(pp)
    if x1 <= cx <= x2 and y1 <= cy <= y2:
        out.append(f'<text x="{px(cx):.1f}" y="{py(cy):.1f}" fill="#c9d4e0" font-size="{max(ppm*0.9,9):.0f}" font-family="monospace" text-anchor="middle" opacity="0.8">{fp_ref}</text>')

out.append('</svg>')
open(OUT, 'w').write('\n'.join(out))
print('wrote', OUT, W, H)
