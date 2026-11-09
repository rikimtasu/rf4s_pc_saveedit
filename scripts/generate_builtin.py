"""Build the compact editor catalog and PNG icons from a game copy, read only."""
import argparse
import gzip
import io
import json
from pathlib import Path
import re
import struct
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image
import pefile
from scripts.game_sources import GameSource, all_references

ROOT = Path(__file__).resolve().parents[1]


def icon_names(executable, count):
    """Read the ordered UTF-16 icon filename vector; do not guess from models.

    Audited build: item 0 at RVA 0x97DD44, stride 0x100. The Switch-named
    .bntx resources have matching .texture members in the PC bundle.
    """
    pe = pefile.PE(str(executable))
    offset = pe.__data__.find('I_Crop00.bntx'.encode('utf-16-le'))
    if offset < 256: raise ValueError('Item icon filename table was not found.')
    base = pe.get_rva_from_offset(offset) - 256
    names = []
    for index in range(count):
        name = pe.get_data(base + index * 256, 256).decode('utf-16-le', errors='ignore').split('\0')[0]
        if not re.fullmatch(r'I_[A-Za-z0-9_]+\.bntx', name): raise ValueError(f'Unrecognized icon filename record {index}.')
        names.append(name.removesuffix('.bntx') + '.texture')
    pe.close()
    if names[:2] != ['I_Empty.texture', 'I_Crop00.texture']: raise ValueError('Unrecognized item icon table ordering.')
    return names


def texture_image(data):
    """Decode the first BC7 PIXL image, excluding relocation data at the end.

    Resource-layout facts corroborated with darkxex's texture extractor and
    local samples. This is an independent reader; no extractor code is copied.
    """
    if len(data) < 64 or data[:4] != b'RES\0': raise ValueError('Expected a RES texture.')
    pixel = data.find(b'PIXL')
    if pixel < 0 or pixel + 84 > len(data): raise ValueError('Missing PIXL image descriptor.')
    width, height = struct.unpack_from('<II', data, pixel + 36)
    size, = struct.unpack_from('<I', data, pixel + 80)
    offset = struct.unpack_from('<I', data, 48)[0] + 16
    end = struct.unpack_from('<I', data, 16)[0]
    expected = ((width + 3) // 4) * ((height + 3) // 4) * 16
    if not 0 < width <= 4096 or not 0 < height <= 4096 or size != expected or offset + size > end or end > len(data):
        raise ValueError('Invalid BC7 image dimensions or bounds.')
    return Image.frombytes('RGBA', (width, height), data[offset:offset + size], 'bcn', 7).transpose(Image.Transpose.ROTATE_90)


def build(game, destination):
    output = Path(destination); output.mkdir(parents=True, exist_ok=True)
    source = GameSource(game)
    references = all_references(game)
    references['items']['source'] = 'Bundled RF4S editor catalog'
    members = {name for entry in source.entries for name in entry['files']}
    icons = {'items': {}, 'people': {}}
    files = set()
    for item_id, name in enumerate(icon_names(Path(game) / 'RF4S.exe', len(references['items']['tables']['item']['records']))):
        if name in members:
            icons['items'][str(item_id)] = name.removesuffix('.texture') + '.png'; files.add(name)
    for name in sorted(members):
        match = re.fullmatch(r'(\d\d)_.+_face_000_[Nn][Oo][Rr][Mm][Aa][Ll]\.texture', name)
        if not match: continue
        number = int(match[1])
        npc = number if 1 <= number <= 23 else {27: 24, 28: 25}.get(number)
        if npc is not None:
            icons['people'][str(npc)] = name.removesuffix('.texture') + '.png'; files.add(name)
    with ZipFile(output / 'icons.zip', 'w', ZIP_DEFLATED) as archive:
        for name in sorted(files):
            image = texture_image(source.read(name))
            bounds = image.getbbox()
            if bounds: image = image.crop(bounds)
            image.thumbnail((64, 64), Image.Resampling.LANCZOS)
            data = io.BytesIO(); image.save(data, 'PNG', optimize=True)
            archive.writestr(name.removesuffix('.texture') + '.png', data.getvalue())
    references['icons'] = icons
    payload = json.dumps(references, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    (output / 'references.json.gz').write_bytes(gzip.compress(payload, compresslevel=9, mtime=0))
    print(f'Built standalone catalog: {len(references["languages"]["languages"])} languages, '
          f'{len(icons["items"])} item icon mappings, {len(icons["people"])} portraits, {len(files)} PNG images.')
    return references


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'builtin')
    args = parser.parse_args()
    build(args.game, args.output)


if __name__ == '__main__': main()
