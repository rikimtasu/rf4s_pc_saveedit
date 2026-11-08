"""Read local recipe definitions for the save editor; never writes the game directory."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor' / 'rf4-modkit'))
import bplist

FILES = ['Acce', 'Armor', 'CookFry', 'CookHandmade', 'CookKnife', 'CookMixer', 'CookOven', 'CookPan', 'CookSteamer', 'Drug', 'Farm', 'Hat', 'Shield', 'Shoes', 'WeaponA', 'WeaponB', 'WeaponC', 'WeaponD', 'WeaponK', 'WeaponM', 'WeaponN']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'web' / 'local-save-reference.js')
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.game.resolve()):
        parser.error('Reference output must be outside the game directory.')
    bundle = (args.game / 'Bundle').resolve()
    manifest = bplist.load(bundle / 'Manifest.plist')
    entries = sorted(manifest['bundles'], key=lambda e: {'bundlePatch2.mbundle': 0, 'bundlePatch1.mbundle': 1}.get(e['bundleName'], 2))
    tables = []
    for suffix in FILES:
        kind = 'rf3Recipe' + suffix
        filename = kind + '.bin'
        loose = sorted(bundle.rglob(filename))
        if loose:
            data = loose[0].read_bytes()
        else:
            entry = next(e for e in entries if filename in e['files'])
            info = entry['files'][filename]
            archive = (bundle / entry['bundleName']).resolve()
            if not archive.is_relative_to(bundle) or info['offset'] < 0 or info['size'] > 1024 * 1024 or info['offset'] + info['size'] > archive.stat().st_size:
                raise ValueError('Invalid archive bounds')
            with archive.open('rb') as stream:
                stream.seek(info['offset'])
                data = stream.read(info['size'])
        groups, end, count = struct.unpack_from('<3I', data, 16)
        if data[:4] != b'NLCL' or groups != 1 or count > 1000 or end != 28 + count * 20 or end > len(data):
            raise ValueError(f'Invalid recipe table: {filename}')
        records = []
        for index in range(1, count):
            result, level, bit = struct.unpack_from('<H12xHI', data, 28 + index * 20)
            if result:
                records.append({'index': index, 'result': result, 'level': level, 'bitOffset': 4096 + 0x426 + bit})
        tables.append({'kind': kind, 'records': records})
        print(f'Read {filename}: {len(records)} recipes')
    args.output.write_text('export const LOCAL_SAVE_REFERENCE = ' + json.dumps({'recipes': tables}, separators=(',', ':')) + ';\n', encoding='utf-8')
    print(f'Created {args.output}; game files unchanged.')


if __name__ == '__main__':
    main()
