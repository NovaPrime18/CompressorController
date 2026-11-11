import json, sys, re
d=json.load(open('audit/netlist.json'))
comps,nets=d['components'],d['nets']
def show(prefixes, hide_power=True):
    for n in sorted(nets):
        if not any(n.startswith(p) for p in prefixes): continue
        print(f"\n● {n}")
        for x in sorted(nets[n], key=lambda y:y['ref']):
            c=comps.get(x['ref'],{})
            print(f"    {x['ref']:>6s}.{x['pin']:<3s} {c.get('value','')[:22]:22s} {x['pinname']}")
if __name__=='__main__':
    show(sys.argv[1:] or ['/PFC/'])
