"""Read-only disassembly for auditing this PC save format. Requires pefile/capstone."""
import argparse
from bisect import bisect_right
from pathlib import Path
import re

import capstone
import pefile

SLOT_BUFFER = 0xE728F8
SLOT_SIZE = 140424


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path)
    parser.add_argument('--function', type=lambda value: int(value, 0))
    parser.add_argument('--start', type=lambda value: int(value, 0))
    parser.add_argument('--length', type=lambda value: int(value, 0), default=0x200)
    parser.add_argument('--refs', type=lambda value: int(value, 0))
    parser.add_argument('--span', type=lambda value: int(value, 0), default=1)
    parser.add_argument('--contains', help='Regex to match disassembly operands')
    args = parser.parse_args()
    pe = pefile.PE(str(args.exe))
    ranges = sorted((entry.struct.BeginAddress, entry.struct.EndAddress) for entry in pe.DIRECTORY_ENTRY_EXCEPTION)
    starts = [start for start, _ in ranges]
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    decoder.skipdata = True

    def function_at(address):
        index = bisect_right(starts, address) - 1
        return ranges[index] if index >= 0 and address < ranges[index][1] else (address, address + args.length)

    def targets(address, size, operands):
        found = []
        match = re.search(r'rip ([+-]) (0x[\da-f]+)', operands)
        if match:
            found.append(address + size + int(match[2], 16) * (-1 if match[1] == '-' else 1))
        if 'rip' not in operands:
            found.extend(int(value, 16) for value in re.findall(r'\+ (0x[\da-f]+)\]', operands))
        return found

    if args.refs is not None or args.contains:
        for section in pe.sections:
            if not section.Characteristics & 0x20000000:
                continue
            for address, size, mnemonic, operands in decoder.disasm_lite(section.get_data(), section.VirtualAddress):
                values = targets(address, size, operands)
                if (args.refs is not None and any(args.refs <= value < args.refs + args.span for value in values)) or (args.contains and re.search(args.contains, operands)):
                    start, end = function_at(address)
                    print(f'{address:08X} function {start:08X}..{end:08X}: {mnemonic} {operands}')
        return
    start, end = function_at(args.function) if args.function is not None else (args.start, args.start + args.length)
    print(f'Function/range {start:08X}..{end:08X}')
    for address, size, mnemonic, operands in decoder.disasm_lite(pe.get_data(start, end - start), start):
        annotations = [f'save+0x{value - SLOT_BUFFER:X}' for value in targets(address, size, operands) if SLOT_BUFFER <= value < SLOT_BUFFER + SLOT_SIZE]
        suffix = ' ; ' + ', '.join(annotations) if annotations else ''
        print(f'{address:08X}: {mnemonic:8} {operands}{suffix}')


if __name__ == '__main__':
    main()
