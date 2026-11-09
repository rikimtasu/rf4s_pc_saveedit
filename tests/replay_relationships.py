"""Read-only replay of saved NPC relationship loading and live dating queries.

Uses the audited RF4S instructions; does not launch/attach to the game or render UI.
Requires pefile, capstone and unicorn. Resource names are not bundled.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

import capstone
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_RAX, UC_X86_REG_RBX, UC_X86_REG_RCX,
                              UC_X86_REG_RDX, UC_X86_REG_RDI, UC_X86_REG_R8,
                              UC_X86_REG_R9, UC_X86_REG_R10, UC_X86_REG_R11,
                              UC_X86_REG_R15, UC_X86_REG_RIP, UC_X86_REG_RSP)

from replay_appearance import AUDITED_EXE_SHA256

NPC_NAMES = {1: 'Vishnal', 2: 'Clorica', 4: 'Forte', 5: 'Kiel', 7: 'Margaret',
             8: 'Dylas', 9: 'Arthur', 11: 'Xiao Pai', 13: 'Amber', 15: 'Doug',
             17: 'Dolce', 20: 'Leon'}


def replay(executable, data):
    if hashlib.sha256(executable.read_bytes()).hexdigest() != AUDITED_EXE_SHA256:
        raise ValueError('Re-audit addresses before using another executable build.')
    if len(data) not in (140424, 140416) or struct.unpack_from('<I', data)[0] != zlib.crc32(data[4:-224]):
        raise ValueError('Expected a checksum-valid PC / extracted Switch slot.')
    pe = pefile.PE(str(executable))
    base = pe.OPTIONAL_HEADER.ImageBase
    uc = Uc(UC_ARCH_X86, UC_MODE_64)
    uc.mem_map(base, (pe.OPTIONAL_HEADER.SizeOfImage + 4095) & ~4095)
    uc.mem_write(base, pe.get_memory_mapped_image())
    actors, table, stack = 0x60000000, 0x60030000, 0x70000000
    uc.mem_map(actors, 0x40000)
    uc.mem_map(stack, 0x10000)
    uc.mem_write(base + 0xe728f8, data)
    uc.mem_write(base + 0xe9c490, struct.pack('<Q', table))
    for npc in range(1, 24):
        actor = actors + npc * 0x1000
        uc.mem_write(table + npc * 8, struct.pack('<Q', actor))
        uc.mem_write(actor, bytes([npc]))
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    allowed = [(0x7fd73, 0x7fe88), (0x227ab0, 0x227ade), (0x2082f4, 0x208366)]

    def instruction(machine, address, size, _):
        rva = address - base
        if not any(start <= rva < end for start, end in allowed):
            raise RuntimeError(f'Replay escaped audited relationship paths: {rva:#x}')
        decoded = next(decoder.disasm(bytes(machine.mem_read(address, size)), address))
        if decoded.mnemonic == 'call':
            raise RuntimeError(f'Unexpected external call: {rva:#x}')

    uc.hook_add(UC_HOOK_CODE, instruction)

    def run(start, end, registers):
        for register, value in registers.items():
            uc.reg_write(register, value)
        uc.emu_start(base + start, base + end, count=10000)
        if uc.reg_read(UC_X86_REG_RIP) != base + end:
            raise RuntimeError('Audited relationship path did not finish.')

    run(0x7fd73, 0x7fe88, {
        UC_X86_REG_RSP: stack + 0x8000, UC_X86_REG_R11: table,
        UC_X86_REG_R9: table + 8, UC_X86_REG_R8: 1, UC_X86_REG_R15: 0,
        UC_X86_REG_RBX: 0xfdff, UC_X86_REG_RDI: 0xf7f7,
        UC_X86_REG_RDX: base + 0xe728f8 + 0x1db40 + 5,
        UC_X86_REG_R10: base + 0xe728f8 + 0x21924,
    })
    result = {'scope': 'Actual NPC load, dating predicate and saved address selection; no UI/story execution.',
              'storedGender': data[0x36], 'people': []}
    for npc, name in NPC_NAMES.items():
        actor = actors + npc * 0x1000
        uc.mem_write(stack + 0x8000, struct.pack('<Q', base + 0x227ade))
        run(0x227ab0, 0x227ade, {UC_X86_REG_RSP: stack + 0x8000, UC_X86_REG_RCX: npc})
        dating = bool(uc.reg_read(UC_X86_REG_RAX) & 255)
        run(0x2082f4, 0x208366, {UC_X86_REG_RBX: npc})
        address = uc.reg_read(UC_X86_REG_RAX) & 65535
        result['people'].append({'id': npc, 'name': name, 'dating': dating,
                                 'npcCallsPlayer': address,
                                 'playerCallsNpc': uc.mem_read(actor + 0x38, 1)[0],
                                 'friendshipPoints': struct.unpack('<i', uc.mem_read(actor + 0xc, 4))[0]})
    pe.close()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('save', type=Path)
    parser.add_argument('--expect-no-dating', type=int, nargs='+', default=[])
    parser.add_argument('--expect-default-address', type=int, nargs='+', default=[])
    args = parser.parse_args()
    original = args.save.read_bytes()
    result = replay(args.executable, original)
    assert args.save.read_bytes() == original, 'Original save changed'
    print(json.dumps(result, indent=2))
    by_id = {person['id']: person for person in result['people']}
    for npc in args.expect_no_dating:
        assert not by_id[npc]['dating'], f'{by_id[npc]["name"]} still has active dating status'
    for npc in args.expect_default_address:
        expected = (23 if result['storedGender'] == 0 else 70) + npc
        assert by_id[npc]['npcCallsPlayer'] == expected, f'{by_id[npc]["name"]} still has a non-default address'
        expected_player = (0 if result['storedGender'] == 0 else 47) + npc
        assert by_id[npc]['playerCallsNpc'] == expected_player, f'Player still uses a special address for {by_id[npc]["name"]}'
    print('PASS: requested relationship assertions; original unchanged. In-game verification still required.')


if __name__ == '__main__':
    main()
