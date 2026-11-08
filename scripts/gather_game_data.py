"""Read four game tables into local reference data. Never writes the game folder."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor' / 'rf4-modkit'))
import bplist


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', type=Path)
    args = parser.parse_args()
    bundle = (args.game / 'Bundle').resolve()
    schema = json.loads((ROOT / 'vendor' / 'venti' / 'schema.json').read_text(encoding='utf-8'))
    manifest = bplist.load(bundle / 'Manifest.plist')
    entries = manifest['bundles']
    entries = sorted(entries, key=lambda entry: {'bundlePatch2.mbundle': 0, 'bundlePatch1.mbundle': 1}.get(entry['bundleName'], 2))
    output = {'source': 'Local game copy · read only', 'tables': {}}
    for kind in ['item', 'equipment', 'use', 'upgrade']:
        table = schema[kind]
        filename = table['variants'][0]['file']
        loose = sorted(bundle.rglob(filename))
        if loose:
            data = loose[0].read_bytes()
        else:
            entry = next(entry for entry in entries if filename in entry['files'])
            meta = entry['files'][filename]
            archive = (bundle / entry['bundleName']).resolve()
            if not archive.is_relative_to(bundle):
                raise ValueError('Manifest archive escapes the game Bundle directory')
            offset, size = int(meta['offset']), int(meta['size'])
            if offset < 0 or not 28 <= size <= 16 * 1024 * 1024 or offset + size > archive.stat().st_size:
                raise ValueError(f'Invalid manifest bounds for {filename}')
            with archive.open('rb') as stream:
                stream.seek(offset)
                data = stream.read(size)
        if data[:4] != b'NLCL' or len(data) < 28:
            raise ValueError(f'{filename}: expected an NLCL table')
        groups, end, count = struct.unpack_from('<3I', data, 16)
        if groups != 1 or 28 + count * table['size'] != end or end > len(data):
            raise ValueError(f'{filename}: record layout does not match the Venti definition')
        records = []
        for index in range(count):
            record = {}
            for field, spec in table['fields'].items():
                start = 28 + index * table['size'] + spec['offset']
                value = int.from_bytes(data[start:start + spec['bits'] // 8], 'little', signed=spec['signed'])
                record[field] = (value >> spec['shift']) & 15 if 'shift' in spec else value
            records.append(record)
        output['tables'][kind] = {'filename': filename, 'count': count, 'sha256': hashlib.sha256(data).hexdigest(), 'records': records}
        print(f'Read {filename}: {count} records, {table["size"]} bytes each. Game files unchanged.')
    destination = ROOT / 'web' / 'local-game-data.js'
    destination.write_text('export const LOCAL_GAME_DATA = ' + json.dumps(output, separators=(',', ':')) + ';\n', encoding='utf-8')
    print(f'Local reference metadata written to {destination}')


if __name__ == '__main__':
    main()
