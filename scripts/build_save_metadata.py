"""Read game symbols and CT descriptions as data for save-editor metadata. No hooks run."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor' / 'rf4-modkit'))
import bplist


def read_entry(game, name):
    bundle = (game / 'Bundle').resolve()
    manifest = bplist.load(bundle / 'Manifest.plist')
    entries = sorted(manifest['bundles'], key=lambda entry: {'bundlePatch2.mbundle': 0, 'bundlePatch1.mbundle': 1}.get(entry['bundleName'], 2))
    entry = next(entry for entry in entries if name in entry['files'])
    meta = entry['files'][name]
    archive = (bundle / entry['bundleName']).resolve()
    if not archive.is_relative_to(bundle):
        raise ValueError('Archive escapes Bundle directory')
    with archive.open('rb') as stream:
        stream.seek(meta['offset'])
        return stream.read(meta['size'])


def variables(data):
    if data[:4] != b'EMDb':
        raise ValueError('Expected EMDb')
    count, start = struct.unpack_from('<2I', data, 24)
    names_base = struct.unpack_from('<I', data, 52)[0]
    out = []
    for index in range(count):
        pointer, _, jp, bit, meta, _ = struct.unpack_from('<6I', data, start + 4 + index * 24)
        if not names_base <= pointer < len(data):
            raise ValueError('Invalid symbol pointer')
        name = data[pointer:data.index(0, pointer)].decode('ascii')
        width = (meta >> 8) & 255
        label = data[jp:data.index(0, jp)].decode('cp932', errors='replace') if names_base <= jp < len(data) else ''
        if not 1 <= width <= 32 or bit + width > 4096:
            raise ValueError(f'Invalid symbol bounds: {name}')
        out.append({'name': name, 'bitOffset': bit, 'width': width, 'description': label})
    return out


def ct_flags(path, symbols):
    output, rejected = [], []
    root = ET.parse(path).getroot()
    occupied = {bit: variable for variable in symbols for bit in range(variable['bitOffset'], variable['bitOffset'] + variable['width'])}

    def walk(parent, groups=()):
        for entry in parent.findall('CheatEntries/CheatEntry'):
            name = entry.findtext('Description', '').strip('"')
            address = entry.findtext('Address', '')
            offsets = [offset.text for offset in entry.findall('Offsets/Offset')]
            if address == 'RF4S_TablePTR_Address' and len(offsets) == 2 and offsets[1] == '8' and entry.findtext('VariableType') == 'Binary':
                try:
                    bit = int(offsets[0], 16) * 8 + int(entry.findtext('BitStart'))
                    width = int(entry.findtext('BitLength'))
                except (ValueError, TypeError):
                    rejected.append(name)
                    continue
                overlapping = [occupied[b] for b in range(bit, bit + width) if b in occupied]
                match = next((variable for variable in overlapping if variable['bitOffset'] == bit and variable['width'] == width), None)
                if width != 1 or bit >= 6656 or overlapping and not match:
                    rejected.append(name)
                else:
                    categories = ['Story Event Flags', 'Other Event Flags', 'Story Barrier Flags', 'Dungeon Barrier Flags', 'Airship Locations', 'Chest Flags', 'Daily Flags', 'Order Flags', 'Requests', 'Character Unlocks']
                    group = next((group for group in groups if group in categories), 'Reference flags')
                    output.append({'name': match['name'] if match else f'CT_BIT_{bit}', 'bitOffset': bit, 'width': 1, 'label': name, 'group': group, 'source': path.name})
            walk(entry, (*groups, name))

    walk(root)
    return output, rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', type=Path)
    parser.add_argument('--table', type=Path, help='Optional CT labels, read as data; no attachment path is assumed.')
    args = parser.parse_args()
    data = read_entry(args.game, 'emdeb.bin')
    symbols = variables(data)
    flags, rejected = ct_flags(args.table, symbols) if args.table else ([], [])
    output = {'symbols': symbols, 'ctFlags': flags, 'rejectedCT': rejected, 'emdebSha256': hashlib.sha256(data).hexdigest(), 'ctSha256': hashlib.sha256(args.table.read_bytes()).hexdigest() if args.table else None}
    (ROOT / 'web' / 'save-metadata.js').write_text('export const SAVE_METADATA = ' + json.dumps(output, ensure_ascii=True, separators=(',', ':')) + ';\n', encoding='utf-8')
    print(f'{len(symbols)} developer symbols; {len(flags)} mapped CT single-bit descriptions; rejected {rejected}. No game/save/table files changed.')
    print('Subevent registers:', [variable for variable in symbols if 'SUBEV' in variable['name'] and variable['width'] > 1][:12])


if __name__ == '__main__':
    main()
