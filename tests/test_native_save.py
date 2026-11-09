import ctypes
import importlib.util
import os
from pathlib import Path
import struct
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = importlib.util.find_spec('PySide6') is not None and (ROOT / 'web' / 'native-bundle.js').is_file()


@unittest.skipUnless(AVAILABLE, 'Native build dependencies / compiled core are not installed')
class NativeSaveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name == 'nt': ctypes.WinDLL(str(Path(os.environ['SystemRoot']) / 'System32' / 'icuuc.dll'))
        from PySide6.QtCore import QCoreApplication
        cls.app = QCoreApplication.instance() or QCoreApplication([])
        from native_save import NativeSave
        cls.backend_type = NativeSave

    def setUp(self):
        self.save = self.backend_type()
        self.original = bytes(self.save.call('demoBytes'))
        self.save.open(self.original, 'synthetic.sav')

    def test_original_round_trip_and_conversion(self):
        self.assertEqual(self.save.build(), self.original)
        self.save.call('setPlayer', changes={'money': 1234})
        self.save.call('setCalendar', changes={'day': 30, 'season': 3, 'year': 4})
        output = self.save.build(platform='switch', experimental=True)
        self.assertEqual(len(output), 140416)
        self.assertEqual(struct.unpack_from('<I', output)[0], zlib.crc32(output[4:-224]))
        self.assertEqual(struct.unpack_from('<i', output, 0x4c)[0], 1234)
        self.assertEqual(bytes(self.save.call('original')), self.original)
        self.save.call('undo'); self.save.call('undo')
        self.assertEqual(self.save.build(), self.original)

    def test_marshaled_attachments_and_element_masks(self):
        records = [{'category': 51, 'max_stack': 9} for _ in range(1024)]
        records[328] = {'category': 15, 'max_stack': 1}
        references = {'tables': {'item': {'count': 1024, 'records': records}, 'equipment': {'count': 1024, 'records': [{'gear_params': 0} for _ in range(1024)]}}}
        self.save.call('references', items=references)
        self.save.call('setItem', container='bag', slot=0, changes={'id': 328, 'quantity': 1}, details={'craft0': 839, 'element': 1})
        item = self.save.call('item', container='bag', slot=0)
        self.assertEqual(item['details']['craft0'], 839)
        self.assertEqual(item['details']['upgrade0'], 872)
        self.assertEqual(item['details']['upgrade1'], 872)
        self.assertEqual(item['element'], 1)
        self.assertEqual(item['level'], 3)
        self.assertEqual(self.save.state()['undo'], 1)
        before = self.save.call('working')
        with self.assertRaises(ValueError):
            self.save.call('setItem', container='bag', slot=0, changes={'id': 328, 'quantity': 1}, details={'craft0': 1024})
        self.assertEqual(self.save.call('working'), before)

    def test_marriage_flags_and_full_width_story_register(self):
        self.save.call('setMarriage', candidate=17, changes={'spouse': 17, 'season': 3, 'day': 30})
        self.assertEqual(self.save.call('marriage', candidate=17)['spouse'], 17)
        self.save.call('setFlag', name='REG_MAIN_SCENARIO', value=511)
        main = next(field for field in self.save.call('flags') if field['name'] == 'REG_MAIN_SCENARIO')
        self.assertEqual(main['value'], 511)
        before = self.save.call('working')
        with self.assertRaises(ValueError): self.save.call('setMarriage', candidate=17, changes={'spouse': 3})
        self.assertEqual(self.save.call('working'), before)

    def test_monster_utf8_codec_has_no_browser_dependency(self):
        data = bytearray(self.original)
        data[0x1bdb0:0x1bdb0 + 6] = '小羊'.encode('utf-8')
        struct.pack_into('<I', data, 0x1bdb0 + 32, 0x1000)
        struct.pack_into('<I', data, 0, zlib.crc32(data[4:-224]))
        self.save.open(data, 'monster.sav')
        self.assertEqual(self.save.call('monsters')[0]['name'], '小羊')

    def test_system_signature_and_flags(self):
        data = bytearray(9304); data[:4] = b'RF4D'
        struct.pack_into('<I', data, 4, zlib.crc32(data[8:]))
        self.save.open(data, 'rf4_sys.sav')
        self.save.call('setSystem', changes={'2': 1, '3': 1})
        output = self.save.build()
        self.assertEqual(output[:4], b'RF4D')
        self.assertEqual(struct.unpack_from('<I', output, 8)[0], 12)
        self.assertEqual(struct.unpack_from('<I', output, 4)[0], zlib.crc32(output[8:]))


if __name__ == '__main__': unittest.main()
