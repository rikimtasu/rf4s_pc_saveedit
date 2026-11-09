"""Read-only replay of the actual RF4S NPC friendship loaders and level getter.

No game process is launched or attached; only audited instructions run in Unicorn.
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
    UC_X86_REG_RDX, UC_X86_REG_RDI, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_R10,
    UC_X86_REG_R11, UC_X86_REG_R12, UC_X86_REG_R15, UC_X86_REG_RIP, UC_X86_REG_RSP)

from replay_appearance import AUDITED_EXE_SHA256

NPC_NAMES = ['Player', 'Vishnal', 'Clorica', 'Volkanon', 'Forte', 'Kiel', 'Bado',
             'Margaret', 'Dylas', 'Arthur', 'Porcoline', 'Xiao Pai', 'Lin Fa', 'Amber',
             'Illuminata', 'Doug', 'Blossom', 'Dolce', 'Jones', 'Nancy', 'Leon',
             'Ventuswill', 'Son', 'Daughter', 'Barrett', 'Raven']


class FriendshipReplay:
    def __init__(self, executable):
        if hashlib.sha256(executable.read_bytes()).hexdigest() != AUDITED_EXE_SHA256:
            raise ValueError('Re-audit addresses before using another executable build.')
        pe = pefile.PE(str(executable))
        self.base = pe.OPTIONAL_HEADER.ImageBase
        self.uc = Uc(UC_ARCH_X86, UC_MODE_64)
        self.uc.mem_map(self.base, (pe.OPTIONAL_HEADER.SizeOfImage + 4095) & ~4095)
        self.uc.mem_write(self.base, pe.get_memory_mapped_image())
        pe.close()
        self.actors, self.table, self.stack = 0x60000000, 0x60030000, 0x70000000
        self.uc.mem_map(self.actors, 0x40000)
        self.uc.mem_map(self.stack, 0x10000)
        self.uc.mem_write(self.base + 0xe9c490, struct.pack('<Q', self.table))
        for npc in range(1, 24):
            actor = self.actors + npc * 0x1000
            self.uc.mem_write(self.table + npc * 8, struct.pack('<Q', actor))
            self.uc.mem_write(actor, bytes([npc]))
        decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        allowed = [(0x7fc96, 0x7fd2e), (0x7fd73, 0x7fe88), (0x2279b0, 0x227aae)]
        checked = set()

        def instruction(machine, address, size, _):
            if address in checked: return
            rva = address - self.base
            if not any(start <= rva < end for start, end in allowed):
                raise RuntimeError(f'Replay escaped audited friendship paths: {rva:#x}')
            decoded = next(decoder.disasm(bytes(machine.mem_read(address, size)), address))
            if decoded.mnemonic == 'call':
                raise RuntimeError(f'Unexpected external call: {rva:#x}')
            checked.add(address)

        self.uc.hook_add(UC_HOOK_CODE, instruction)

    def run(self, start, end, registers):
        for register, value in registers.items(): self.uc.reg_write(register, value)
        self.uc.emu_start(self.base + start, self.base + end, count=10000)
        if self.uc.reg_read(UC_X86_REG_RIP) != self.base + end:
            raise RuntimeError('Audited friendship path did not finish.')

    def load(self, data):
        if len(data) not in (140424, 140416) or struct.unpack_from('<I', data)[0] != zlib.crc32(data[4:-224]):
            raise ValueError('Expected a checksum-valid PC / extracted Switch slot.')
        self.uc.mem_write(self.base + 0xe728f8, bytes(data))
        self.run(0x7fc96, 0x7fd2e, {UC_X86_REG_R12: self.base})
        self.run(0x7fd73, 0x7fe88, {
            UC_X86_REG_RSP: self.stack + 0x8000, UC_X86_REG_R11: self.table,
            UC_X86_REG_R9: self.table + 8, UC_X86_REG_R8: 1, UC_X86_REG_R15: 0,
            UC_X86_REG_RBX: 0xfdff, UC_X86_REG_RDI: 0xf7f7,
            UC_X86_REG_RDX: self.base + 0xe728f8 + 0x1db40 + 5,
            UC_X86_REG_R10: self.base + 0xe728f8 + 0x21924,
        })

    def returned_level(self, start, value):
        self.uc.mem_write(self.stack + 0x8000, struct.pack('<Q', self.base + 0x227aae))
        self.run(start, 0x227aae, {UC_X86_REG_RSP: self.stack + 0x8000, UC_X86_REG_RCX: value})
        return self.uc.reg_read(UC_X86_REG_RAX) & 65535

    def level(self, npc):
        if not 1 <= npc <= 25: raise ValueError('Expected NPC id 1–25.')
        return self.returned_level(0x227a40, npc)

    def points_to_level(self, points):
        return self.returned_level(0x2279b0, points)

    def people(self):
        return [{'id': npc, 'name': NPC_NAMES[npc], 'level': self.level(npc)} for npc in range(1, 26)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('save', type=Path)
    args = parser.parse_args()
    original = args.save.read_bytes()
    replay = FriendshipReplay(args.executable)
    replay.load(original)
    print(json.dumps({'scope': 'Actual NPC loaders and friendship getter; no UI/story execution.',
                      'people': replay.people()}, indent=2))
    assert args.save.read_bytes() == original, 'Original save changed'


if __name__ == '__main__': main()
