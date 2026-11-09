"""Read-only replay of system-save player-name restoration and the default getter.

Uses actual audited instructions. The two language probes are explicit stubs;
actor gender is a synthetic runtime input. No game process or files are modified.
"""
import hashlib
from pathlib import Path
import struct
import zlib

import capstone
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_RAX, UC_X86_REG_RDX, UC_X86_REG_R12,
    UC_X86_REG_R15, UC_X86_REG_RIP, UC_X86_REG_RSP)

from replay_appearance import AUDITED_EXE_SHA256


class PlayerNameReplay:
    def __init__(self, executable):
        if hashlib.sha256(executable.read_bytes()).hexdigest() != AUDITED_EXE_SHA256:
            raise ValueError('Re-audit addresses before using another executable build.')
        pe = pefile.PE(str(executable))
        self.base = pe.OPTIONAL_HEADER.ImageBase
        self.uc = Uc(UC_ARCH_X86, UC_MODE_64)
        self.uc.mem_map(self.base, (pe.OPTIONAL_HEADER.SizeOfImage + 4095) & ~4095)
        self.uc.mem_write(self.base, pe.get_memory_mapped_image()); pe.close()
        self.actor, self.stack = 0x60000000, 0x70000000
        self.uc.mem_map(self.actor, 0x1000); self.uc.mem_map(self.stack, 0x10000)
        self.uc.mem_write(self.base + 0xe15078, struct.pack('<Q', self.actor))
        self.uc.mem_write(self.base + 0xe94f6c, bytes(4))
        self.japanese = False
        decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        allowed = [(0x7f79f, 0x7f7f0), (0x89a30, 0x89b27), (0x21f6d0, 0x21f6e7)]

        def instruction(machine, address, size, _):
            rva = address - self.base
            if rva in (0x25a400, 0x25a660):
                machine.reg_write(UC_X86_REG_RAX, int(self.japanese) if rva == 0x25a660 else 0)
                rsp = machine.reg_read(UC_X86_REG_RSP)
                machine.reg_write(UC_X86_REG_RIP, struct.unpack('<Q', machine.mem_read(rsp, 8))[0])
                machine.reg_write(UC_X86_REG_RSP, rsp + 8)
                return
            if not any(start <= rva < end for start, end in allowed):
                raise RuntimeError(f'Replay escaped audited player-name paths: {rva:#x}')
            decoded = next(decoder.disasm(bytes(machine.mem_read(address, size)), address))
            if decoded.mnemonic == 'call' and decoded.op_str not in (
                hex(self.base + 0x89a30), hex(self.base + 0x25a400), hex(self.base + 0x25a660)):
                raise RuntimeError(f'Unexpected external call: {rva:#x}')

        self.uc.hook_add(UC_HOOK_CODE, instruction)

    def run(self, start, end, registers):
        for register, value in registers.items(): self.uc.reg_write(register, value)
        self.uc.emu_start(self.base + start, self.base + end, count=10000)
        if self.uc.reg_read(UC_X86_REG_RIP) != self.base + end:
            raise RuntimeError('Audited player-name path did not finish.')

    def load(self, data):
        if len(data) != 9304 or data[:4] != b'RF4D' or struct.unpack_from('<I', data, 4)[0] != zlib.crc32(data[8:]):
            raise ValueError('Expected a checksum-valid system save.')
        self.uc.mem_write(self.base + 0xe704a0, bytes(data))

    def name(self, record, gender='male', japanese=False):
        if not 0 <= record < 40 or gender not in ('male', 'female'): raise ValueError('Invalid replay input.')
        self.japanese = japanese
        bank, slot = divmod(record, 20)
        self.uc.mem_write(self.actor + 0x238, struct.pack('<I', 0x8000000 if gender == 'male' else 0))
        flags = struct.unpack('<I', self.uc.mem_read(self.base + 0xe704b0, 4))[0]
        self.uc.mem_write(self.base + 0xe704b0, struct.pack('<I', flags & ~0x40 | bank << 6))
        self.uc.mem_write(self.base + 0xe704b4 + bank * 2, struct.pack('<H', slot))
        self.uc.mem_write(self.base + 0xe94e60, bytes(19))
        self.run(0x7f79f, 0x7f7f0, {UC_X86_REG_R12: self.base, UC_X86_REG_R15: 0, UC_X86_REG_RSP: self.stack + 0x8000})
        self.uc.mem_write(self.stack + 0x8000, struct.pack('<Q', self.base + 0x89b27))
        self.run(0x89a30, 0x89b27, {UC_X86_REG_RSP: self.stack + 0x8000})
        address = self.uc.reg_read(UC_X86_REG_RAX)
        return bytes(self.uc.mem_read(address, 19)).split(b'\0')[0].decode('utf-8')

    def transfer_unlocked(self):
        self.uc.mem_write(self.stack + 0x8000, struct.pack('<Q', self.base + 0x21f6e7))
        self.run(0x21f6d0, 0x21f6e7, {UC_X86_REG_RDX: self.actor + 0x400, UC_X86_REG_RSP: self.stack + 0x8000})
        return bool(struct.unpack('<I', self.uc.mem_read(self.actor + 0x440, 4))[0])
