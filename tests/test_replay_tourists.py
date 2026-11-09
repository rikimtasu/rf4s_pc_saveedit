"""Optional replay of the actual counter loader and script-visible tourist getter."""
import base64
import importlib.util
import os
from pathlib import Path
import struct
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXECUTABLE = os.environ.get('RF4S_EXE')
AVAILABLE = bool(EXECUTABLE) and all(importlib.util.find_spec(name) for name in ('pefile', 'unicorn'))


@unittest.skipUnless(AVAILABLE, 'Set RF4S_EXE and install read-only replay dependencies')
class TouristReplayTests(unittest.TestCase):
    def test_exports_reach_the_actual_tourist_getter_and_leave_order_points_unchanged(self):
        import pefile
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_HOOK_CODE
        from unicorn.x86_const import UC_X86_REG_RDX, UC_X86_REG_RSP
        pe = pefile.PE(EXECUTABLE); base = pe.OPTIONAL_HEADER.ImageBase
        uc = Uc(UC_ARCH_X86, UC_MODE_64)
        uc.mem_map(base, (pe.OPTIONAL_HEADER.SizeOfImage + 4095) & ~4095)
        uc.mem_write(base, pe.get_memory_mapped_image()); pe.close()
        stack = 0x70000000; uc.mem_map(stack, 0x10000)
        def audit(machine, address, size, _):
            rva = address - base
            if not (0x80018 <= rva < 0x8003e or 0x21e050 <= rva < 0x21e061):
                raise RuntimeError(f'Replay escaped audited tourist paths: {rva:#x}')
        uc.hook_add(UC_HOOK_CODE, audit)
        for count in [0, 12345, 99999999]:
            program = """
                import {createDemo} from './web/save-core.js';
                const save=createDemo(); save.setPlayer({tourists:Number(process.argv[1]),prince_points:123});
                process.stdout.write(Buffer.from(save.build()).toString('base64'));
            """
            data = base64.b64decode(subprocess.check_output(['node', '--input-type=module', '-e', program, str(count)], cwd=ROOT))
            uc.mem_write(base + 0xe728f8, data)
            uc.emu_start(base + 0x80018, base + 0x8003e, count=1000)
            self.assertEqual(struct.unpack('<i', uc.mem_read(base + 0xe9ac08, 4))[0], 123)
            uc.reg_write(UC_X86_REG_RDX, stack + 0x1000); uc.reg_write(UC_X86_REG_RSP, stack + 0x8000)
            uc.mem_write(stack + 0x8000, struct.pack('<Q', base + 0x21e061))
            uc.emu_start(base + 0x21e050, base + 0x21e061, count=1000)
            self.assertEqual(struct.unpack('<i', uc.mem_read(stack + 0x1040, 4))[0], count)
