"""Compare JavaScript save output with pinned upstream on synthetic bytes."""
import base64
import importlib.util
import json
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'vendor' / 'rf4-modkit' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    upstream = load_module('save')
    flags_module = load_module('emflags')
    original = bytearray((i * 31 + 7) & 255 for i in range(upstream.SAVE_SIZE))
    for name, value in [('day', 9), ('season', 0), ('year', 1)]:
        struct.pack_into('<I', original, upstream.SCALARS[name][0], value)
    original = upstream.SaveFile(original).build()
    calendar = {'day': 30, 'season': 3, 'year': 1234}
    flags = [
        {'name': 'REG_MAIN_SCENARIO', 'bitOffset': 0, 'width': 9, 'value': 104},
        {'name': 'FLG_TEST', 'bitOffset': 9, 'width': 1, 'value': 1},
        {'name': 'REG_WIDE', 'bitOffset': 13, 'width': 32, 'value': 4294967295},
    ]
    variables = [flags_module.Variable(flag['name'], '', flag['bitOffset'], flag['width']) for flag in flags]
    table = flags_module.EmFlagTable(variables)
    expected = upstream.SaveFile(original)
    for name, value in calendar.items():
        expected.set(name, value)
    for flag in flags:
        expected.set_flag(flag['name'], flag['value'], emf=table)
    request = {'bytes': base64.b64encode(original).decode(), 'calendar': calendar, 'flags': flags}
    result = subprocess.run(['node', str(ROOT / 'tests' / 'parity.mjs')], input=json.dumps(request), capture_output=True, text=True, check=True, cwd=ROOT)
    actual = json.loads(result.stdout)
    output = base64.b64decode(actual['output'])
    assert output == expected.build(), 'JavaScript export differs from upstream Python'
    assert actual['values'] == [expected.flag(flag['name'], emf=table) for flag in flags]
    assert upstream.SaveFile(output).crc_ok()
    assert output[upstream.CRC_DATA_START + upstream.CRC_DATA_LEN:] == original[upstream.CRC_DATA_START + upstream.CRC_DATA_LEN:]
    print('PASS: JavaScript matches upstream Python byte for byte; CRC, MSB-first flags and trailing bytes verified.')


if __name__ == '__main__':
    main()
