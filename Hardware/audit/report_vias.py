import sys, math
from collections import Counter, defaultdict
sys.path.insert(0, '/home/tj/CompressorController/Hardware/audit')
from parse_board import parse, find_all, get

s = open('/home/tj/CompressorController/Hardware/CompressorController.kicad_pcb').read()
b = parse(s)

vias = find_all(b, 'via')
print("=== ZONES ===")
for z in find_all(b, 'zone'):
    net = get(z, 'net'); lay = get(z, 'layer')
    name = get(z, 'name')
    print(' zone', net[1] if net else '?', lay[1] if lay else [x for x in z if isinstance(x,list) and x[0]=='layer'][:2],
          'name=', name[1] if name else '', 'priority=', get(z,'priority'))

print("\n=== VIAS BY NET: free/not, size, drill, layers ===")
grp = defaultdict(list)
for v in vias:
    net = get(v, 'net')
    nm = net[1] if net else '?'
    at = get(v, 'at'); size = get(v, 'size'); drill = get(v,'drill')
    layers = get(v, 'layers'); free = get(v, 'free')
    grp[nm].append((float(get(v,'at')[1]), float(get(v,'at')[2]),
                    size[1] if size else '?', drill[1] if drill else '?',
                    ' '.join(layers[1:]) if layers else '?', free[1] if free else 'no'))
for nm, lst in sorted(grp.items(), key=lambda kv: -len(kv[1])):
    sigs = Counter((x[2], x[3], x[4], x[5]) for x in lst)
    print(f' {nm}: {len(lst)}')
    for sig, cnt in sigs.items():
        print('    size/drill/layers/free =', sig, 'count', cnt)
