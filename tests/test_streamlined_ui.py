"""Native UX and standalone catalog checks; exports only inside temporary folders."""
import ctypes
import importlib.util
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = importlib.util.find_spec('PySide6') is not None and (ROOT / 'web/native-bundle.js').is_file()


@unittest.skipUnless(AVAILABLE, 'Native build dependencies are not installed')
class StreamlinedUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name == 'nt': ctypes.WinDLL(str(Path(os.environ['SystemRoot']) / 'System32' / 'icuuc.dll'))
        else: os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from native_ui import NativeWindow
        with patch('native_ui.QSettings') as settings:
            settings.return_value.value.return_value = 'en'
            self.window = NativeWindow()
        self.window.testing = True; self.window.test_errors = []
        self.original = bytes(self.window.backend.call('demoBytes'))
        self.window.open_bytes(self.original, 'rf4_s01.sav')
        self.window.show()

    def tearDown(self):
        self.window.closing = True; self.window.close(); self.window.deleteLater(); self.app.processEvents()

    def select(self, key):
        self.window.navigation.setCurrentRow(self.window.pages[key][2])
        for _ in range(3): self.app.processEvents()

    def edit(self, form, field, value):
        form.write(field, value); form.track(field)

    def test_no_opt_in_or_demo_button_and_valid_drafts_save_with_a_backup(self):
        from PySide6.QtWidgets import QCheckBox, QPushButton
        captions = [obj.text() for obj in self.window.findChildren(QCheckBox)]
        self.assertNotIn('Enable editing', captions)
        self.assertFalse(any('synthetic' in obj.text().lower() for obj in self.window.findChildren(QPushButton)))
        self.select('player')
        self.assertTrue(self.window.player_form.controls['tourists'].isEnabled())
        self.edit(self.window.player_form, 'tourists', '12345')
        self.select('friendship')
        selector = self.window.record_selectors['friendship']; selector.setCurrentIndex(selector.findData(24))
        self.edit(self.window.record_forms['friendship'], 'level', 10)
        self.assertTrue(self.window.export_action.isEnabled())
        with tempfile.TemporaryDirectory() as temp, patch.dict('os.environ', {'APPDATA': temp}), patch('native_ui.QFileDialog.getSaveFileName') as dialog:
            folder = Path(temp) / 'Rune Factory 4 Special'; folder.mkdir()
            target = folder / 'rf4_s01.sav'; target.write_bytes(self.original)
            self.window.export_file()
            self.assertEqual(self.window.test_errors, [])
            dialog.assert_not_called()
            output = target.read_bytes()
            self.assertEqual(struct.unpack_from('<i', output, 0x20714)[0], 12345)
            self.assertEqual(struct.unpack_from('<H', output, 0x1df6c)[0] >> 2, 10)
            self.assertEqual(struct.unpack_from('<I', output)[0], zlib.crc32(output[4:-224]))
            self.assertEqual(next(folder.glob('*.bak')).read_bytes(), self.original)
        self.assertFalse(self.window.pending())
        self.assertEqual(self.window.backend.state()['undo'], 1)
        self.window.backend.call('undo'); self.assertEqual(bytes(self.window.backend.call('working')), self.original)

    def test_invalid_last_draft_leaves_all_working_bytes_and_disk_unchanged(self):
        self.select('player'); self.edit(self.window.player_form, 'tourists', 123)
        self.select('calendar'); self.edit(self.window.calendar_form, 'day', 99)
        with tempfile.TemporaryDirectory() as temp, patch.dict('os.environ', {'APPDATA': temp}):
            folder = Path(temp) / 'Rune Factory 4 Special'; folder.mkdir()
            target = folder / 'rf4_s01.sav'; target.write_bytes(self.original)
            self.window.export_file()
            self.assertTrue(self.window.test_errors)
            self.assertEqual(target.read_bytes(), self.original)
            self.assertEqual(list(folder.glob('*.bak')), [])
        self.assertEqual(bytes(self.window.backend.call('working')), self.original)
        self.assertEqual(self.window.player_form.drafts, {'tourists': '123'})
        self.assertEqual(self.window.calendar_form.drafts, {'day': '99'})

    def test_switching_records_applies_the_previous_valid_draft_without_a_prompt(self):
        self.select('friendship')
        self.edit(self.window.record_forms['friendship'], 'level', 27)
        self.window.record_selectors['friendship'].setCurrentIndex(4)
        self.assertEqual(self.window.selections['friendship'], 5)
        self.assertEqual(self.window.backend.call('friendship')[0]['level'], 27)
        self.assertFalse(self.window.record_forms['friendship'].drafts)

    @unittest.skipUnless((ROOT / 'builtin/references.json.gz').is_file(), 'Prepare the real standalone catalog first')
    def test_bundled_references_and_icons_work_without_reading_any_game_folder(self):
        with patch('native_ui.all_references', side_effect=AssertionError('Runtime game reading is unnecessary')):
            self.assertEqual(self.window.language_combo.count(), 7)
            self.assertEqual(len(self.window.backend.call('items')), 1107)  # Empty item 0 is represented by Clear slot.
            from native_save import local_references
            expected = sum(len(table['records']) for table in local_references()['recipes']['recipes'])
            self.assertEqual(len(self.window.backend.call('recipes')), expected)
            self.assertGreater(expected, 0)
            self.assertEqual(len(self.window.nickname_names()), 186)
            self.select('inventory')
            selector = self.window.inventory_form.controls['id']
            self.assertFalse(selector.itemIcon(selector.findData(328)).isNull())
            self.assertFalse(self.window.icons.icon('items', 839).isNull())
            self.select('relationships')
            self.assertFalse(self.window.record_selectors['relationships'].itemIcon(0).isNull())
