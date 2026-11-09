"""Read-only targeted instruction lookup for gender/dialogue diagnosis."""
import argparse
import re
import capstone
import pefile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable')
    parser.add_argument('--refs', type=lambda value: int(value, 0))
    parser.add_argument('--match')
    args = parser.parse_args()
    if args.refs is None and not args.match:
        parser.error('Provide --refs or --match.')
    pe = pefile.PE(args.executable)
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    ranges = sorted((entry.struct.BeginAddress, entry.struct.EndAddress) for entry in pe.DIRECTORY_ENTRY_EXCEPTION)
    hits = 0
    for start, end in ranges:
        instructions = list(decoder.disasm_lite(pe.get_data(start, end - start), start))
        for index, (address, size, mnemonic, operands) in enumerate(instructions):
            match = re.search(r'rip ([+-]) (0x[\da-f]+)', operands)
            reference = address + size + int(match[2], 16) * (-1 if match[1] == '-' else 1) if match else None
            if not (args.refs is not None and reference == args.refs or args.match and re.search(args.match, operands)):
                continue
            hits += 1
            print(f'Function {start:#x}..{end:#x}')
            for row in instructions[max(0, index - 3):index + 4]:
                print(f'{row[0]:08X}: {row[2]} {row[3]}')
    print(f'{hits} matching instructions')
    pe.close()


if __name__ == '__main__':
    main()
