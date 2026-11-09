import ctypes
import importlib.util
import os
from pathlib import Path
import struct
import unittest
from unittest.mock import patch
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

    def test_state_snapshot_is_reused_until_a_successful_mutation(self):
        snapshot = self.save.state()
        snapshot['calendar']['day'] = 99
        self.assertEqual(self.save.state()['calendar']['day'], 9, 'Callers must not mutate the cached snapshot')
        with patch.object(self.save, '_evaluate', wraps=self.save._evaluate) as evaluate:
            self.save.state(); self.save.state()
            self.assertEqual(evaluate.call_count, 0, 'Read-only state queries rescan the whole save')
        self.save.call('setPlayer', changes={'money': 1234})
        self.assertEqual(self.save.state()['exportState'], 'unexported')
        self.save.call('markExported')
        self.assertEqual(self.save.state()['exportState'], 'exported')
        self.save.call('undo')
        self.assertEqual(self.save.state()['exportState'], 'unexported')
        self.save.call('redo')
        self.assertEqual(self.save.state()['exportState'], 'exported')
        self.save.call('reset')
        self.assertFalse(self.save.state()['dirty'])
        self.save.open(self.original, 'new.sav')
        self.assertEqual(self.save.state()['exportState'], 'original')
        revision = self.save.revision
        with self.assertRaises(ValueError): self.save.call('setCalendar', changes={'day': 99, 'season': 0, 'year': 1})
        self.assertEqual(self.save.revision, revision)
        self.assertEqual(self.save.state()['calendar']['day'], 9)
        self.save.apply_callbacks([lambda: self.save.call('setPlayer', changes={'money': 345})])
        self.assertGreater(self.save.revision, revision)
        self.assertTrue(self.save.state()['dirty'])

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
        self.assertEqual(struct.unpack_from('<I', output, 16)[0], 12)
        self.assertEqual(struct.unpack_from('<I', output, 8)[0], 0)
        self.assertEqual(struct.unpack_from('<I', output, 4)[0], zlib.crc32(output[8:]))

    def test_marshaled_dating_cleanup_is_export_only(self):
        self.save.call('setNumber', offset=0x1db48, type='u32', value=0x400302)
        self.save.call('patchBytes', offset=0x1db4c, text='61')
        before = self.save.call('working')
        self.assertEqual([person['id'] for person in self.save.call('datingCleanup', gender='male')], [1, 5, 8, 9, 15, 20])
        output = self.save.build(gender='male', resetDating=True)
        self.assertEqual(struct.unpack_from('<I', output, 0x1db48)[0], 0x302)
        self.assertEqual(output[0x1db4c], 24)
        self.assertEqual(struct.unpack_from('<I', output)[0], zlib.crc32(output[4:-224]))
        self.assertEqual(self.save.call('working'), before)

    def test_marshaled_guest_friendship_uses_real_save_fields_and_preserves_header(self):
        self.save.call('setNumber', offset=0x1df38, type='u16', value=0xa5a5)
        self.save.call('setNumber', offset=0x1df6c, type='u16', value=3)
        self.save.call('setNumber', offset=0x1df74, type='u16', value=2)
        before = self.save.call('working')
        for npc, level in [(24, 10), (25, 27)]: self.save.call('setFriendship', id=npc, level=level)
        for options in [{}, {'platform': 'switch', 'experimental': True}]:
            output = self.save.build(**options)
            self.assertEqual(struct.unpack_from('<H', output, 0x1df6c)[0], 43)
            self.assertEqual(struct.unpack_from('<H', output, 0x1df74)[0], 110)
            self.assertEqual(struct.unpack_from('<H', output, 0x1df38)[0], 0xa5a5)
            self.assertEqual(struct.unpack_from('<I', output)[0], zlib.crc32(output[4:-224]))
        people = {person['id']: person for person in self.save.call('friendship')}
        self.assertEqual(people[24]['level'], 10)
        self.assertEqual(people[25]['level'], 27)
        self.save.call('undo'); self.save.call('undo')
        self.assertEqual(self.save.call('working'), before)
        self.assertEqual(bytes(self.save.call('original')), self.original)

    def test_marshaled_relationship_edits_preserve_other_bits_and_are_atomic(self):
        self.save.call('setNumber', offset=0x1db48, type='u32', value=0xad000302)
        self.save.call('setNumber', offset=0x1db54, type='u32', value=0xbeef807f)
        before = self.save.call('working')
        self.save.call('setRelationship', id=1, changes={'dating': 1, 'npcCallsPlayer': 97, 'playerCallsNpc': 133})
        person = self.save.call('relationships')[0]
        self.assertEqual((person['dating'], person['npcCallsPlayer'], person['playerCallsNpc']), (1, 97, 133))
        output = self.save.build()
        self.assertEqual(struct.unpack_from('<I', output, 0x1db48)[0], 0xad400302)
        self.assertEqual(struct.unpack_from('<I', output, 0x1db54)[0], 0xbeef807f | 133 << 7)
        self.assertEqual(struct.unpack_from('<I', output)[0], zlib.crc32(output[4:-224]))
        self.save.call('undo'); self.assertEqual(self.save.call('working'), before)
        with self.assertRaises(ValueError): self.save.call('setRelationship', id=1, changes={'dating': 1, 'playerCallsNpc': 186})
        self.assertEqual(self.save.call('working'), before)
        self.assertEqual(bytes(self.save.call('original')), self.original)

    def test_native_name_codec_handles_unicode_and_default_reset_in_system_saves(self):
        data = bytearray(9304); data[:4] = b'RF4D'
        struct.pack_into('<I', data, 8, 1)
        data[0x504:0x508] = b'Lest'
        struct.pack_into('<I', data, 4, zlib.crc32(data[8:]))
        self.save.open(data, 'rf4_sys.sav')
        self.save.call('setPlayerName', id=0, name='一二三四五六')
        self.assertEqual(self.save.call('playerNames')[0]['name'], '一二三四五六')
        self.assertTrue(self.save.call('playerNames')[0]['valid'])
        output = self.save.build()
        self.assertEqual(output[0x504:0x517], '一二三四五六'.encode('utf-8') + b'\0')
        self.assertEqual(struct.unpack_from('<I', output, 8)[0], 1)
        self.save.call('setPlayerName', id=0, name='')
        self.assertTrue(self.save.call('playerNames')[0]['usesDefault'])
        self.save.call('undo')
        self.assertEqual(self.save.call('playerNames')[0]['name'], '一二三四五六')
        before = self.save.call('working')
        with self.assertRaises(ValueError): self.save.call('setPlayerName', id=0, name='1234567')
        self.assertEqual(self.save.call('working'), before)
        self.assertEqual(bytes(self.save.call('original')), bytes(data))

    def test_read_only_item_and_flag_previews_preserve_working_bytes_and_history(self):
        items = [{'category': 51, 'max_stack': 9} for _ in range(1024)]
        items[328] = {'category': 15, 'max_stack': 1}
        gear = [{'gear_params': 0} for _ in range(1024)]
        gear[328] = {'gear_params': 0, 'attack': 5, 'poison_atk': 2048}
        self.save.call('references', items={'tables': {'item': {'count': 1024, 'records': items}, 'equipment': {'count': 1024, 'records': gear}}})
        self.save.call('setFlag', name='REG_MAIN_SCENARIO', value=442)
        self.save.call('setPlayer', changes={'money': 500}); self.save.call('undo')
        before, state = self.save.call('working'), self.save.state()
        item = self.save.call('previewItem', container='bag', slot=0, details={'upgrade0': 839})
        self.assertEqual(item['after']['item']['level'], 2)
        self.assertFalse(item['after']['exactFinalStats'])
        self.assertEqual(next(effect['value'] for effect in item['after']['sections'][0]['effects'] if effect['field'] == 'poison_atk'), 50)
        flags = self.save.call('flagImpact', name='REG_MAIN_SCENARIO', value=430)
        self.assertTrue(flags['rewind']); self.assertFalse(flags['simulatedEvents'])
        self.assertEqual(self.save.call('working'), before)
        self.assertEqual(self.save.state()['undo'], state['undo'])
        self.assertEqual(self.save.state()['redo'], state['redo'])


if __name__ == '__main__': unittest.main()
