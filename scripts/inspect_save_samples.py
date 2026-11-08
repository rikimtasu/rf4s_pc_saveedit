"""Read-only save and Cheat Engine table inspection. Never executes table scripts."""
import argparse
import hashlib
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
import zlib


def inspect_save(path):
    data = path.read_bytes()
    print(f'{path}: {len(data)} bytes; SHA-256 {hashlib.sha256(data).hexdigest()}')
    if data[:4] == b'RF4D':
        print('System checksum:', hex(struct.unpack_from('<I', data, 4)[0]), hex(zlib.crc32(data[8:])))
    else:
        print('Slot checksum:', hex(struct.unpack_from('<I', data)[0]), hex(zlib.crc32(data[4:-224])))
    for start, size in [(0x1ec04, 96), (0x20680, 208), (0x21920, 32), (0x21a90, 48)]:
        if start >= len(data):
            continue
        for offset in range(start, start + size, 16):
            print(f'{offset:05X}: {data[offset:offset + 16].hex(" ")}')
    print('Last nonzero byte:', hex(max(i for i, byte in enumerate(data) if byte)))


def inspect_table(path):
    root = ET.parse(path).getroot()

    def entries(parent, groups=()):
        for entry in parent.findall('CheatEntries/CheatEntry'):
            name = entry.findtext('Description', '').strip('"')
            address = entry.findtext('Address', '')
            offsets = [offset.text for offset in entry.findall('Offsets/Offset')]
            if entry.findtext('GroupHeader') == '1':
                print('GROUP:', ' / '.join((*groups, name)))
            elif address and any(word in ' / '.join((*groups, name)).lower() for word in ['event', 'request', 'currency', 'unlock', 'story']):
                bits = (entry.findtext('BitStart'), entry.findtext('BitLength'))
                print('FIELD:', ' / '.join((*groups, name)), address, offsets, 'bits', bits)
            entries(entry, (*groups, name))

    print('TABLE:', path)
    entries(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+', type=Path)
    args = parser.parse_args()
    for path in args.paths:
        if path.suffix.lower() == '.ct':
            inspect_table(path)
        else:
            inspect_save(path)


if __name__ == '__main__':
    main()
