import json, uuid, shutil, time, re, os

PCB = '/home/tj/CompressorController/Hardware/CompressorController.kicad_pcb'
plan = json.load(open('/home/tj/CompressorController/Hardware/audit/via_plan.json'))

def num(v):
    s = f'{v:.6f}'.rstrip('0').rstrip('.')
    return s if s not in ('-0', '') else '0'

src = open(PCB).read()
assert src.rstrip().endswith(')')

# backup
stamp = time.strftime('%Y%m%d-%H%M%S')
bak = f'/home/tj/CompressorController/Hardware/CompressorController-backups/CompressorController.kicad_pcb.{stamp}.before-vias'
shutil.copy2(PCB, bak)
print('backup:', bak)

blocks = []
for v in plan['vias']:
    free = '\t\t(free yes)\n' if v['net'] == 'GND' else ''
    blocks.append(
        f'\t(via\n'
        f'\t\t(at {num(v["x"])} {num(v["y"])})\n'
        f'\t\t(size 0.6)\n'
        f'\t\t(drill 0.3)\n'
        f'\t\t(layers "F.Cu" "B.Cu")\n'
        f'{free}'
        f'\t\t(net "{v["net"]}")\n'
        f'\t\t(uuid "{uuid.uuid4()}")\n'
        f'\t)\n')
for s in plan['segs']:
    blocks.append(
        f'\t(segment\n'
        f'\t\t(start {num(s["x1"])} {num(s["y1"])})\n'
        f'\t\t(end {num(s["x2"])} {num(s["y2"])})\n'
        f'\t\t(width {num(s["w"])})\n'
        f'\t\t(layer "{s["layer"]}")\n'
        f'\t\t(net "{s["net"]}")\n'
        f'\t\t(uuid "{uuid.uuid4()}")\n'
        f'\t)\n')

# insert just before the final closing paren line
i = src.rstrip().rfind(')')
head = src[:i]
new = head + ''.join(blocks) + src[i:]
open(PCB, 'w').write(new)
print(f'inserted {len(plan["vias"])} vias and {len(plan["segs"])} segments')
print('new file size', os.path.getsize(PCB))
