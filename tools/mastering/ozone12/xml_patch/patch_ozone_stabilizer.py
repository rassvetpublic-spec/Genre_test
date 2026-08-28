#!/usr/bin/env python3
"""Patch confirmed Ozone 12 Stabilizer T/S params for PluginVer 120002 / Build 1331.
Calibration-only values are never defaults.
"""
import argparse, xml.etree.ElementTree as ET

def fmt(x): return f"{float(x):.8f}".replace('.', ',')

def block(root):
    b=root.find('Stabilizer')
    if b is None: raise SystemExit('Stabilizer block not found')
    return b

def setp(b,pid,val,add=False):
    for p in b.findall('Param'):
        if p.get('ParamID')==pid:
            old=p.get('Value'); p.set('Value', str(val) if pid in ('Target','ProcessingMode') else fmt(val)); return old
    if add:
        e=ET.Element('Param',{'ElementID':'Stabilizer','ParamID':pid,'Value':str(val) if pid in ('Target','ProcessingMode') else fmt(val)})
        extra=b.find('ExtraBytes'); idx=list(b).index(extra) if extra is not None else len(b); b.insert(idx,e); return '<added>'
    raise SystemExit(f'Missing confirmed ParamID {pid}; rerun with --add-missing if PluginVer/Build is confirmed')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('input_xml'); ap.add_argument('output_xml')
    ap.add_argument('--baseline-ts',action='store_true',help='Set confirmed 25/50/50/100/100/100 on both T and S')
    ap.add_argument('--t',nargs=6,type=float,metavar=('AMOUNT','SPEED','SMOOTH','LOW','MID','HIGH'))
    ap.add_argument('--s',nargs=6,type=float,metavar=('AMOUNT','SPEED','SMOOTH','LOW','MID','HIGH'))
    ap.add_argument('--target',type=int)
    ap.add_argument('--add-missing',action='store_true')
    args=ap.parse_args()
    tree=ET.parse(args.input_xml); root=tree.getroot()
    if root.get('PluginVer')!='120002' or root.get('PluginBuild')!='1331':
        raise SystemExit(f"Unsupported/unconfirmed build: PluginVer={root.get('PluginVer')} Build={root.get('PluginBuild')}")
    b=block(root); changed=[]
    if args.baseline_ts:
        args.t=args.s=[25,50,50,100,100,100]
    if args.t or args.s:
        changed.append(('ProcessingMode',setp(b,'ProcessingMode',2,args.add_missing),'2'))
    names=['Amount','Speed','FreqSmoothing','LFStrength','MFStrength','HFStrength']
    if args.t:
        for pid,val in zip(names,args.t): changed.append((pid,setp(b,pid,val,args.add_missing),fmt(val)))
    if args.s:
        for pid,val in zip(names,args.s):
            q='Aux: '+pid; changed.append((q,setp(b,q,val,args.add_missing),fmt(val)))
    if args.target is not None: changed.append(('Target',setp(b,'Target',args.target,args.add_missing),str(args.target)))
    tree.write(args.output_xml,encoding='utf-8',xml_declaration=True)
    print('Wrote',args.output_xml)
    for r in changed: print('\t'.join(map(str,r)))
if __name__=='__main__': main()
