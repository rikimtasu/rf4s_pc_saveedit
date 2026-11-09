"""Read reference tables from an RF4S game copy without modifying it."""
from pathlib import Path
import struct
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor' / 'rf4-modkit'))
import bplist

LANGUAGES = {'eng': ('en', 'English'), 'jpn': ('ja', '日本語'), 'fra': ('fr', 'Français'),
             'deu': ('de', 'Deutsch'), 'kor': ('ko', '한국어'),
             'twn': ('zh-Hant', '繁體中文'), 'chn': ('zh-Hans', '简体中文')}
NAME_TABLES = {'rf3TxtItem_split2_1': 'items', 'rf3TxtNpc_split2_1': 'people',
               'rf3TxtSkill_split2_1': 'skills', 'rf3TxtHeroNickName': 'nicknames'}


class GameSource:
    def __init__(self, game):
        self.bundle = (Path(game) / 'Bundle').resolve()
        manifest = bplist.load(self.bundle / 'Manifest.plist')
        self.entries = sorted(manifest['bundles'], key=lambda e: {'bundlePatch2.mbundle': 0, 'bundlePatch1.mbundle': 1}.get(e['bundleName'], 2))

    def read(self, filename):
        loose = sorted(self.bundle.rglob(filename))
        if loose:
            target = loose[0].resolve()
            if not target.is_relative_to(self.bundle) or target.stat().st_size > 16 * 1024 * 1024:
                raise ValueError('Invalid loose reference file')
            return target.read_bytes()
        entry = next((e for e in self.entries if filename in e['files']), None)
        if entry is None:
            return None
        info = entry['files'][filename]
        archive = (self.bundle / entry['bundleName']).resolve()
        offset, size = int(info['offset']), int(info['size'])
        if not archive.is_relative_to(self.bundle) or offset < 0 or not 0 < size <= 16 * 1024 * 1024 or offset + size > archive.stat().st_size:
            raise ValueError(f'Invalid archive bounds: {filename}')
        with archive.open('rb') as stream:
            stream.seek(offset)
            data = stream.read(size)
        if len(data) != size:
            raise ValueError(f'Truncated reference: {filename}')
        return data


def parse_text(data):
    if len(data) < 8 or data[:4] != b'TEXT':
        raise ValueError('Expected an extracted TEXT language table')
    count, = struct.unpack_from('<I', data, 4)
    end = 8 + count * 8
    if count > 10000 or end > len(data):
        raise ValueError('Invalid TEXT record count')
    result = []
    for index in range(count):
        size, offset = struct.unpack_from('<II', data, 8 + index * 8)
        if offset < end or size > 65536 or offset + size >= len(data) or data[offset + size] != 0:
            raise ValueError('Invalid TEXT string bounds')
        result.append(data[offset:offset + size].decode('utf-8'))
    return result


def parse_name_table(kind, data):
    names = parse_text(data)
    if kind == 'nicknames' and len(names) != 186:
        raise ValueError('Unrecognized nickname table layout.')
    return names


def language_references(source):
    languages = {}
    for suffix, (code, label) in LANGUAGES.items():
        tables = {}
        for name, kind in NAME_TABLES.items():
            data = source.read(f'{name}.{suffix}')
            if data is not None:
                tables[kind] = parse_name_table(kind, data)
        if tables:
            languages[code] = {'label': label, **tables}
    return {'languages': languages}


def item_references(source):
    schema = json.loads((ROOT / 'vendor' / 'venti' / 'schema.json').read_text(encoding='utf-8'))
    tables = {}
    for kind in ['item', 'equipment', 'use', 'upgrade']:
        table = schema[kind]
        filename = table['variants'][0]['file']
        data = source.read(filename)
        if data is None:
            continue
        if len(data) < 28 or data[:4] != b'NLCL':
            raise ValueError(f'Invalid reference table: {filename}')
        groups, end, count = struct.unpack_from('<3I', data, 16)
        if groups != 1 or not 1 <= count <= 10000 or end != 28 + count * table['size'] or end > len(data):
            raise ValueError(f'Invalid record layout: {filename}')
        records = []
        for index in range(count):
            record = {}
            for name, spec in table['fields'].items():
                offset = 28 + index * table['size'] + spec['offset']
                value = int.from_bytes(data[offset:offset + spec['bits'] // 8], 'little', signed=spec['signed'])
                record[name] = value >> spec['shift'] & 15 if 'shift' in spec else value
            records.append(record)
        tables[kind] = {'filename': filename, 'count': count, 'records': records}
    if 'item' not in tables:
        raise ValueError('Game item definitions were not found.')
    return {'source': 'Your game copy · read only', 'tables': tables}


def recipe_references(source):
    suffixes = ['Acce', 'Armor', 'CookFry', 'CookHandmade', 'CookKnife', 'CookMixer', 'CookOven', 'CookPan', 'CookSteamer', 'Drug', 'Farm', 'Hat', 'Shield', 'Shoes', 'WeaponA', 'WeaponB', 'WeaponC', 'WeaponD', 'WeaponK', 'WeaponM', 'WeaponN']
    tables = []
    for suffix in suffixes:
        kind = 'rf3Recipe' + suffix
        data = source.read(kind + '.bin')
        if data is None:
            continue
        if len(data) < 28 or data[:4] != b'NLCL':
            raise ValueError('Invalid recipe table')
        groups, end, count = struct.unpack_from('<3I', data, 16)
        if groups != 1 or not 1 <= count <= 1000 or end != 28 + count * 20 or end > len(data):
            raise ValueError('Invalid recipe record layout')
        records = []
        for index in range(1, count):
            result, level, bit = struct.unpack_from('<H12xHI', data, 28 + index * 20)
            if result:
                if result > 2047 or not 0 <= bit < 1497:
                    raise ValueError('Invalid recipe result or flag')
                records.append({'index': index, 'result': result, 'level': level, 'bitOffset': 4096 + 0x426 + bit})
        tables.append({'kind': kind, 'records': records})
    return {'recipes': tables}


def all_references(game):
    source = GameSource(game)
    return {'languages': language_references(source), 'items': item_references(source), 'recipes': recipe_references(source)}
