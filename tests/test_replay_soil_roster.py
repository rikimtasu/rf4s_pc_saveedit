"""Narrow read-only machine-code tests; no scene, model or gameplay execution."""
import base64
import hashlib
import importlib.util
import os
from pathlib import Path
import struct
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXECUTABLE = os.environ.get('RF4S_EXE')
AVAILABLE = bool(EXECUTABLE) and all(importlib.util.find_spec(name) for name in ('pefile', 'capstone', 'unicorn'))


@unittest.skipUnless(AVAILABLE, 'Set RF4S_EXE and install read-only replay dependencies')
class SoilRosterReplayTests(unittest.TestCase):
    def machine(self, allowed):
        import capstone
        import pefile
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_HOOK_CODE
        from replay_appearance import AUDITED_EXE_SHA256
        data = Path(EXECUTABLE).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), AUDITED_EXE_SHA256)
        pe = pefile.PE(data=data)
        base = pe.OPTIONAL_HEADER.ImageBase
        uc = Uc(UC_ARCH_X86, UC_MODE_64)
        uc.mem_map(base, (pe.OPTIONAL_HEADER.SizeOfImage + 4095) & ~4095)
        uc.mem_write(base, pe.get_memory_mapped_image())
        uc.mem_map(0x60000000, 0x20000)
        decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        def instruction(machine, address, size, _):
            rva = address - base
            if not any(start <= rva < end for start, end in allowed): raise RuntimeError(f'Escaped audited soil/roster seam: {rva:#x}')
            decoded = next(decoder.disasm(bytes(machine.mem_read(address, size)), address))
            if decoded.mnemonic == 'call': raise RuntimeError(f'Unexpected call in pure copy/count seam: {rva:#x}')
        uc.hook_add(UC_HOOK_CODE, instruction)
        pe.close()
        return uc, base

    def test_all_162_serialized_soil_records_round_trip_through_real_copy_loops(self):
        from unicorn.x86_const import UC_X86_REG_RDI, UC_X86_REG_R13, UC_X86_REG_R14, UC_X86_REG_R11, UC_X86_REG_R9, UC_X86_REG_R10, UC_X86_REG_RDX, UC_X86_REG_R12, UC_X86_REG_RIP
        uc, base = self.machine([(0x7df09, 0x7df59), (0x7fad0, 0x7fb0a)])
        packets = bytes((i * 37 + 11) & 255 for i in range(9 * 18 * 16))
        manager, records = 0x60000000, 0x60001000
        for farm in range(9): uc.mem_write(manager + 0x90 + farm * 8, struct.pack('<Q', records + farm * 18 * 16))
        uc.mem_write(records, packets)
        for register, value in [(UC_X86_REG_RDI, manager), (UC_X86_REG_R13, base), (UC_X86_REG_R14, 0), (UC_X86_REG_R11, 9)]: uc.reg_write(register, value)
        uc.emu_start(base + 0x7df09, base + 0x7df59, count=10000)
        self.assertEqual(uc.reg_read(UC_X86_REG_RIP), base + 0x7df59)
        self.assertEqual(bytes(uc.mem_read(base + 0xe8d7ac, len(packets))), packets)
        uc.mem_write(records, bytes(len(packets)))
        for register, value in [(UC_X86_REG_R9, manager + 0x90), (UC_X86_REG_R10, 9), (UC_X86_REG_RDX, 0), (UC_X86_REG_R12, base)]: uc.reg_write(register, value)
        uc.emu_start(base + 0x7fad0, base + 0x7fb0a, count=10000)
        self.assertEqual(uc.reg_read(UC_X86_REG_RIP), base + 0x7fb0a)
        self.assertEqual(bytes(uc.mem_read(records, len(packets))), packets)

    def test_new_npc_and_monster_records_are_counted_by_real_roster_loop(self):
        from unicorn.x86_const import UC_X86_REG_RDI, UC_X86_REG_RIP
        program = """
            import {createDemo} from './web/save-core.js';
            import {SAVE_METADATA} from './web/save-metadata.js';
            import {RosterEditor} from './web/roster-core.js';
            const save=createDemo(); save.setFlag(SAVE_METADATA.symbols.find(f=>f.name==='REG_MON_HOUSE0_L_LV'),1);
            for(const species of [3,21,48,110]) new RosterEditor(save).add({species,acknowledgeRisk:true});
            process.stdout.write(Buffer.from(save.build()).toString('base64'));
        """
        data = base64.b64decode(subprocess.check_output(['node', '--input-type=module', '-e', program], cwd=ROOT))
        uc, base = self.machine([(0x1e3007, 0x1e3038)])
        uc.mem_write(base + 0xe98fb0, data[0x1bdb0:0x1bdb0 + 200 * 36])
        uc.reg_write(UC_X86_REG_RDI, 0x60000000)
        uc.emu_start(base + 0x1e3007, base + 0x1e3038, count=10000)
        self.assertEqual(uc.reg_read(UC_X86_REG_RIP), base + 0x1e3038)
        self.assertEqual(bytes(uc.mem_read(0x600000fa, 1)), b'\x04')


if __name__ == '__main__': unittest.main()
