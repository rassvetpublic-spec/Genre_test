#!/usr/bin/env python3
import argparse, json, xml.etree.ElementTree as ET
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('xml'); ap.add_argument('--schema',default=str(Path(__file__).with_name('ozone12_confirmed_ts_schema_v1_3.json'))); args=ap.parse_args()
    schema=json.load(open(args.schema,encoding='utf-8')); root=ET.parse(args.xml).getroot(); c=schema['confirmed_for']
    ok=(root.get('PresetVer')==c['PresetVer'] and root.get('PluginVer')==c['PluginVer'] and root.get('PluginBuild')==c['PluginBuild'])
    print('BUILD', 'PASS' if ok else 'REVALIDATE', root.get('PresetVer'),root.get('PluginVer'),root.get('PluginBuild'))
    dup=[]
    for block in root:
        seen=set()
        for p in block.findall('Param'):
            pid=p.get('ParamID')
            if pid in seen: dup.append((block.tag,pid))
            seen.add(pid)
    print('DUPLICATE_PARAMID', 'PASS' if not dup else 'FAIL')
    for x in dup: print(' ',x)
    raise SystemExit(0 if ok and not dup else 2)
if __name__=='__main__': main()
