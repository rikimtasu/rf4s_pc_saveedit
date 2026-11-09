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

RECIPE_FIXTURE = {'recipes': [
    {'kind': 'rf3RecipeAcce', 'records': [
        {'index': 1, 'result': 328, 'level': 1, 'bitOffset': 5158},
        {'index': 2, 'result': 328, 'level': 2, 'bitOffset': 5158},
    ]},
    {'kind': 'rf3RecipeArmor', 'records': [{'index': 1, 'result': 329, 'level': 3, 'bitOffset': 5159}]},
    {'kind': 'rf3RecipeCookHandmade', 'records': [{'index': 1, 'result': 559, 'level': 4, 'bitOffset': 5160}]},
]}


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

    def test_learn_all_shortcut_ignores_filters_and_commits_one_undoable_edit(self):
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        self.window.load_references({'recipes': RECIPE_FIXTURE})
        self.select('recipes')
        self.window.recipe_group.setCurrentIndex(self.window.recipe_group.findData('rf3RecipeAcce'))
        self.window.recipe_search.setText('328')
        self.edit(self.window.record_forms['recipes'], 'known', 1)
        self.assertEqual(len(self.window.filtered_recipes()), 2)
        self.assertTrue(self.window.learn_all_recipes_action.isEnabled())
        self.assertEqual(self.window.learn_all_recipes_action.shortcut().toString(), 'Ctrl+Shift+L')
        self.window.activateWindow(); self.window.setFocus(); self.app.processEvents()
        QTest.keyClick(self.window, Qt.Key.Key_L, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
        self.app.processEvents()
        self.assertTrue(all(recipe['known'] for recipe in self.window.backend.call('recipes')))
        self.assertEqual(self.window.backend.state()['undo'], 1)
        self.assertFalse(self.window.record_forms['recipes'].drafts)
        self.assertEqual(self.window.recipe_search.text(), '328')
        self.window.learn_all_recipes_button.click()
        self.assertEqual(self.window.backend.state()['undo'], 1, 'Learning already-known recipes is a no-op')
        self.window.mutate('undo')
        self.assertEqual(self.window.backend.call('working'), list(self.original))
        self.assertEqual(self.window.test_errors, [])

    def test_learn_all_is_disabled_without_definitions_or_for_system_saves(self):
        self.window.load_references({}); self.window.refresh()
        self.assertFalse(self.window.learn_all_recipes_action.isEnabled())
        with self.assertRaises(ValueError): self.window.bulk_recipes(True, all_recipes=True)
        self.assertEqual(self.window.backend.call('working'), list(self.original))
        data = bytearray(9304); data[:4] = b'RF4D'
        struct.pack_into('<I', data, 4, zlib.crc32(data[8:]))
        self.window.load_references({'recipes': RECIPE_FIXTURE})
        self.window.open_bytes(data, 'rf4_sys.sav')
        self.assertFalse(self.window.learn_all_recipes_action.isEnabled())
        self.window.learn_all_recipes_action.trigger()
        self.assertEqual(self.window.backend.call('working'), list(data))

    def test_failed_learn_all_keeps_the_recipe_draft_and_working_bytes(self):
        self.window.load_references({'recipes': RECIPE_FIXTURE})
        self.select('recipes')
        form = self.window.record_forms['recipes']
        self.edit(form, 'known', 1)
        call = self.window.backend.call
        def reject_bulk(operation, **args):
            if operation == 'setRecipes' and len(args['recipes']) > 1: raise ValueError('Bulk edit rejected')
            return call(operation, **args)
        with patch.object(self.window.backend, 'call', side_effect=reject_bulk):
            self.window.learn_all_recipes_action.trigger()
        self.assertEqual(form.drafts, {'known': 1})
        self.assertEqual(self.window.backend.call('working'), list(self.original))
        self.assertEqual(self.window.backend.state()['undo'], 0)
        self.assertEqual(self.window.test_errors, ['Bulk edit rejected'])

    def test_export_then_undo_to_original_warns_before_close_or_replacement(self):
        from PySide6.QtWidgets import QMessageBox
        self.window.mutate('setPlayer', changes={'money': 1234})
        with tempfile.TemporaryDirectory() as temp, patch.dict('os.environ', {'APPDATA': temp}):
            self.window.export_file()
            self.assertEqual(self.window.test_errors, [])
        self.assertEqual(self.window.backend.state()['exportState'], 'exported')
        self.assertEqual(self.window.document_status.text(), 'Current edits exported')
        self.window.mutate('undo')
        self.assertFalse(self.window.backend.state()['dirty'])
        self.assertEqual(self.window.document_status.text(), 'Unexported changes')
        before = self.window.backend.state()
        self.window.ui_language_combo.setCurrentIndex(self.window.ui_language_combo.findData('zh-CN'))
        self.assertEqual(self.window.document_status.text(), '尚未导出的修改')
        self.assertEqual(self.window.backend.state(), before)
        self.window.ui_language_combo.setCurrentIndex(self.window.ui_language_combo.findData('en'))
        self.assertEqual(self.window.document_status.text(), 'Unexported changes')
        with patch.object(self.window, 'question', return_value=QMessageBox.StandardButton.Cancel) as dialog:
            self.assertFalse(self.window.discard_confirmation())
            dialog.assert_called_once()
        self.window.mutate('redo')
        with patch.object(self.window, 'question') as dialog:
            self.assertTrue(self.window.discard_confirmation())
            dialog.assert_not_called()

    def test_failed_export_and_cancelled_save_as_do_not_acknowledge_pending_changes(self):
        self.select('player'); self.edit(self.window.player_form, 'money', 1234)
        with patch('native_ui.export_to_game_folder', side_effect=OSError('write failed')):
            self.window.export_file()
        self.assertEqual(self.window.backend.state()['exportState'], 'unexported')
        self.assertEqual(self.window.test_errors, ['write failed'])
        with patch('native_ui.QFileDialog.getSaveFileName', return_value=('', '')):
            self.window.save_as()
        self.assertEqual(self.window.backend.state()['exportState'], 'unexported')
        with patch('native_ui.QFileDialog.getSaveFileName', return_value=('copy.sav', '')), patch.object(self.window, 'write_file', side_effect=OSError('copy failed')):
            self.window.save_as()
        self.assertEqual(self.window.backend.state()['exportState'], 'unexported')
        self.assertEqual(self.window.test_errors, ['write failed', 'copy failed'])

    def test_successful_save_as_acknowledges_only_after_write_and_drafts_still_warn(self):
        from PySide6.QtWidgets import QMessageBox
        self.select('player'); self.edit(self.window.player_form, 'money', 1234)
        with tempfile.TemporaryDirectory() as temp, patch('native_ui.QFileDialog.getSaveFileName', return_value=(str(Path(temp) / 'copy.sav'), '')):
            self.window.save_as()
            self.assertTrue((Path(temp) / 'copy.sav').is_file())
        self.assertEqual(self.window.backend.state()['exportState'], 'exported')
        self.edit(self.window.player_form, 'money', '')
        with patch.object(self.window, 'question', return_value=QMessageBox.StandardButton.Cancel):
            self.assertFalse(self.window.discard_confirmation())
        self.window.player_form.clear()
        self.assertTrue(self.window.discard_confirmation())

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
