#!/usr/bin/env python3
"""Validate Ozone 12 ElementChain bytes: 00 + uint32 LE length + UTF-8 name repeated; no count-prefix."""
import argparse, base64, struct, xml.etree.ElementTree as ET

def decode_chain(data):
    b=base64.b64decode(data)
    out=[]; i=0
    while i < len(b):
        if b[i] != 0:
            raise ValueError(f"Invalid marker at byte {i}: expected 00, got {b[i]:02x}")
        i += 1
        if i+4 > len(b):
            raise ValueError('Truncated length')
        n=struct.unpack('<I', b[i:i+4])[0]
        i += 4
        if i+n > len(b):
            raise ValueError(f'Truncated name length {n}')
        name=b[i:i+n].decode('utf-8')
        i += n
        out.append(name)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('xml')
    args=ap.parse_args()
    root=ET.parse(args.xml).getroot()
    chains=[]
    for eb in root.iter('ExtraBytes'):
        if eb.get('ElementID') == 'ElementChain':
            chains.append(eb.get('Data',''))
    if not chains:
        raise SystemExit('No ElementChain found')
    for data in chains:
        names=decode_chain(data)
        print('OK:', ' -> '.join(names))
if __name__ == '__main__':
    main()
