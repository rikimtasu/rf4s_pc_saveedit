"""Replay RF4S's appearance-load branch read-only; not a full game/rendering test.

Requires pefile, capstone and unicorn. Uses the supplied executable's instructions,
with external resource-loading calls captured rather than executing the game.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zlib

import capstone
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RIP, UC_X86_REG_RSP, UC_X86_REG_RSI, UC_X86_REG_RCX, UC_X86_REG_RDX


ROOT = Path(__file__).resolve().parents[1]
BODY_IDS = {'male': 0x4c1, 'female': 0x4d1}
PORTRAIT_IDS = {'male': 0x4c2, 'female': 0x4d2}
AUDITED_EXE_SHA256 = 'cb64f88be1f40ac932607188de85dab98c44f43a6a023c92a85e17dd18a2b803'


def replay(executable, data, initial_gender='male'):
    if initial_gender not in BODY_IDS:
        raise ValueError('Initial actor gender must be male or female.')
    if hashlib.sha256(executable.read_bytes()).hexdigest() != AUDITED_EXE_SHA256:
        raise ValueError('This replay is scoped to the audited RF4S.exe build; re-audit addresses for another build.')
    if len(data) not in (140424, 140416) or struct.unpack_from('<I', data)[0] != zlib.crc32(data[4:-224]):
        raise ValueError('Expected a checksum-valid PC / extracted Switch slot.')
    pe = pefile.PE(str(executable))
    base = pe.OPTIONAL_HEADER.ImageBase
    machine = Uc(UC_ARCH_X86, UC_MODE_64)
    machine.mem_map(base, (pe.OPTIONAL_HEADER.SizeOfImage + 4095) & ~4095)
    machine.mem_write(base, pe.get_memory_mapped_image())
    actor = 0x60000000
    stack = 0x70000000
    machine.mem_map(actor, 0x10000)
    machine.mem_map(stack, 0x10000)
    machine.mem_write(base + 0xe728f8, data)
    machine.mem_write(base + 0xe94f6c, struct.pack('<I', 0))
    machine.mem_write(base + 0xe15078, struct.pack('<Q', actor))
    machine.mem_write(base + 0xe9ac38, data[0x20740:0x20744])
    machine.mem_write(actor + 0x238, struct.pack('<I', 0x08000000 if initial_gender == 'male' else 0))
    machine.mem_write(actor + 0x220, struct.pack('<HH', BODY_IDS[initial_gender], 0x38a1 if initial_gender == 'male' else 0x37af))
    machine.mem_write(actor + 0x22c, struct.pack('<I', PORTRAIT_IDS[initial_gender]))
    machine.reg_write(UC_X86_REG_RSP, stack + 0x8000)
    machine.reg_write(UC_X86_REG_RSI, 0)
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    calls = []
    allowed = [(0x84087, 0x841b1), (0x165eb0, 0x166057), (0x166060, 0x16617a)]

    def instruction(uc, address, size, _):
        rva = address - base
        if not any(start <= rva < end for start, end in allowed):
            raise RuntimeError(f'Replay escaped audited appearance branch at {rva:#x}')
        decoded = next(decoder.disasm(bytes(uc.mem_read(address, size)), address))
        if decoded.mnemonic != 'call':
            return
        if not decoded.op_str.startswith('0x'):
            raise RuntimeError(f'Unexpected indirect call at {rva:#x}')
        target = int(decoded.op_str, 16) - base
        calls.append({'at': hex(rva), 'target': hex(target), 'rcx': uc.reg_read(UC_X86_REG_RCX), 'rdx': uc.reg_read(UC_X86_REG_RDX)})
        if target in (0x165eb0, 0x166060):
            return
        if target == 0x241d70:
            raise RuntimeError('Non-default NPC appearance requires a real NPC table; replay refuses to fake it.')
        if target not in (0xd5ad0, 0x139c60, 0xa6900, 0x16cf80, 0xb0180, 0xa49b0):
            raise RuntimeError(f'Unaudited external call {target:#x}')
        uc.reg_write(UC_X86_REG_RIP, address + size)

    machine.hook_add(UC_HOOK_CODE, instruction)
    machine.emu_start(base + 0x84087, base + 0x841b1, count=2000)
    if machine.reg_read(UC_X86_REG_RIP) != base + 0x841b1:
        raise RuntimeError('Replay did not finish the appearance branch')
    result = {
        'scope': 'Appearance branch only; excludes player initialization and NPC dialogue.',
        'initialActorGender': initial_gender,
        'storedGender': data[0x36],
        'swapFlag': struct.unpack_from('<I', data, 0x38)[0] & 1,
        'outfit': (struct.unpack_from('<I', data, 0x74)[0] >> 18) & 63,
        'appearanceOverride': struct.unpack_from('<i', data, 0x20740)[0],
        'actorGender': 'male' if struct.unpack('<I', machine.mem_read(actor + 0x238, 4))[0] & 0x08000000 else 'female',
        'bodyResource': struct.unpack('<H', machine.mem_read(actor + 0x220, 2))[0],
        'portraitResource': struct.unpack('<I', machine.mem_read(actor + 0x22c, 4))[0],
        'calls': calls,
    }
    pe.close()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('save', type=Path)
    parser.add_argument('--expect', choices=['male', 'female'], required=True)
    parser.add_argument('--initial-gender', choices=['male', 'female'], default='male', help='Actor state before the appearance branch (default: male). Not a full save-load simulation.')
    parser.add_argument('--export-reset', action='store_true', help='Replay current SaveDocument.build gender + appearance reset in memory')
    args = parser.parse_args()
    original = args.save.read_bytes()
    data = original
    if args.export_reset:
        program = "import {readFileSync} from 'node:fs'; import {SaveDocument} from './web/save-core.js'; const save=new SaveDocument(readFileSync(process.argv[1])); process.stdout.write(Buffer.from(save.build({gender:process.argv[2],resetAppearance:true})).toString('base64'));"
        import base64
        data = base64.b64decode(subprocess.check_output(['node', '--input-type=module', '-e', program, str(args.save), args.expect], cwd=ROOT))
    result = replay(args.executable, data, args.initial_gender)
    assert args.save.read_bytes() == original, 'Original save changed during replay'
    result['originalSha256'] = hashlib.sha256(original).hexdigest()
    print(json.dumps(result, indent=2))
    assert result['actorGender'] == args.expect, 'Actor gender did not match requested gender'
    assert result['bodyResource'] == BODY_IDS[args.expect], 'Body still selects the opposite protagonist resource'
    assert result['portraitResource'] == PORTRAIT_IDS[args.expect], 'Portrait still selects the opposite protagonist resource'
    print('PASS: appearance branch matches from the stated initial actor; player initialization and NPC dialogue are NOT tested. Original unchanged.')


if __name__ == '__main__':
    main()
