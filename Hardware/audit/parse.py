#!/usr/bin/env python3
"""Parse KiCad XML netlist into a compact, queryable form."""
import xml.etree.ElementTree as ET
import json, sys, re, collections

XML = "audit/cc.xml"

def load(path=XML):
    t = ET.parse(path)
    r = t.getroot()
    comps = {}
    for c in r.findall(".//components/comp"):
        ref = c.get("ref")
        comps[ref] = {
            "ref": ref,
            "value": (c.findtext("value") or "").strip(),
            "footprint": (c.findtext("footprint") or "").strip(),
            "sheetpath": (c.find("sheetpath").get("names") if c.find("sheetpath") is not None else ""),
            "desc": (c.findtext("description") or "").strip(),
            "props": {p.get("name"): (p.get("value") or "") for p in c.findall("property")},
            "pins": {},
        }
    nets = {}
    for n in r.findall(".//nets/net"):
        name = n.get("name")
        nodes = []
        for node in n.findall("node"):
            ref = node.get("ref")
            nodes.append({
                "ref": ref,
                "pin": node.get("pin"),
                "pinname": (node.findtext("pinfunction") or "").strip(),
                "pintype": node.get("pintype") or "",
            })
            if ref in comps:
                comps[ref]["pins"][node.get("pin")] = {
                    "net": name,
                    "pinname": (node.findtext("pinfunction") or "").strip(),
                    "pintype": node.get("pintype") or "",
                }
        nets[name] = nodes
    return comps, nets

def sheet_names(path):
    return {"/": "root"}

def dump():
    comps, nets = load()
    out = {
        "components": comps,
        "nets": {k: v for k, v in nets.items()},
    }
    with open("audit/netlist.json", "w") as f:
        json.dump(out, f, indent=1)
    print("components:", len(comps), "nets:", len(nets))

if __name__ == "__main__":
    dump()
