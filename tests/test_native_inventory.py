"""Inventory readability and repeated-loading regressions, using synthetic saves."""
import ctypes
import importlib.util
import os
from pathlib import Path
import struct
import time
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = importlib.util.find_spec('PySide6') is not None and (ROOT / 'web/native-bundle.js').is_file()


@unittest.skipUnless(AVAILABLE, 'Native build dependencies / compiled core are not installed')
class NativeInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name == 'nt': ctypes.WinDLL(str(Path(os.environ['SystemRoot']) / 'System32' / 'icuuc.dll'))
        else: os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        from PySide6.QtWidgets import QApplication
        from native_ui import NativeWindow
        cls.app = QApplication.instance() or QApplication([])
        with patch('native_ui.QSettings') as settings:
            settings.return_value.value.return_value = 'en'
            cls.window = NativeWindow()
        if not cls.window.backend.call('items', editableOnly=True):
            records = [{'category': 51, 'max_stack': 9} for _ in range(1024)]
            cls.window.load_references({'items': {'tables': {'item': {'count': 1024, 'records': records}}}})
        cls.window.testing = True; cls.window.test_errors = []
        cls.original = bytearray(cls.window.backend.call('demoBytes'))
        spec = cls.window.constants['inventories']['fridge']
        for slot in range(spec['slots']):
            struct.pack_into('<H', cls.original, spec['offset'] + slot * 28, 753 | (9 << 11))
        struct.pack_into('<I', cls.original, 0, zlib.crc32(cls.original[4:-224]))
        cls.window.show()

    @classmethod
    def tearDownClass(cls):
        cls.window.closing = True; cls.window.close(); cls.window.deleteLater(); cls.app.processEvents()

    def setUp(self):
        self.window.open_bytes(self.original, 'synthetic.sav')
        self.window.navigation.setCurrentRow(self.window.pages['inventory'][2])
        self.window.container_combo.setCurrentIndex(self.window.container_combo.findData('fridge'))
        self.app.processEvents()

    def test_default_text_and_item_picker_icons_are_readable(self):
        self.assertEqual(self.window.font().pointSizeF(), 11, 'Use the compact, readable default without inherited scale inflation')
        self.assertEqual(self.window.inventory_form.labels['id'].font().pointSizeF(), 11)
        self.assertEqual(self.window.inventory_grid.font().pointSizeF(), 11)
        self.assertEqual(self.window.inventory_grid.gridSize().width(), 104)
        self.assertEqual(self.window.inventory_form.controls['id'].iconSize().width(), 24)
        self.assertEqual(self.window.inventory_form.controls['id'].view().iconSize().width(), 24,
                         'Keep picker rows compact while the selected item has a separate larger icon')

    def test_nord_recipe_and_search_popups_have_consistent_readable_colors(self):
        from PySide6.QtGui import QPalette
        recipe_popup = self.window.record_selectors['recipes'].view()
        recipe_popup.ensurePolished()
        self.assertGreater(recipe_popup.palette().color(QPalette.ColorRole.Text).lightness(), 180,
                           'The dark recipe popup still inherits low-contrast brown text')
        for popup in (recipe_popup, self.window.inventory_form.controls['id'].view(), self.window.inventory_form.controls['id'].completer().popup()):
            popup.ensurePolished()
            with self.subTest(popup=popup):
                self.assertEqual(popup.palette().color(QPalette.ColorRole.Base).name(), '#2e3440')
                self.assertEqual(popup.palette().color(QPalette.ColorRole.Text).name(), '#eceff4')
                self.assertEqual(popup.palette().color(QPalette.ColorRole.Highlight).name(), '#88c0d0')
                self.assertEqual(popup.palette().color(QPalette.ColorRole.HighlightedText).name(), '#2e3440')

    def test_additional_windows_reuse_the_installed_fusion_style(self):
        from native_ui import NativeWindow
        from PySide6.QtWidgets import QApplication
        with patch.object(QApplication, 'setStyle', wraps=QApplication.setStyle) as set_style, patch('native_ui.QSettings') as settings:
            settings.return_value.value.return_value = 'en'
            window = NativeWindow()
        window.closing = True; window.close(); window.deleteLater(); self.app.processEvents()
        self.assertEqual(set_style.call_count, 0, 'Recreating Fusion restyles every existing window unnecessarily')

    @unittest.skipUnless((ROOT / 'builtin/icons.zip').is_file(), 'Prepare the bundled icons first')
    def test_catalog_layout_does_not_eagerly_decode_all_item_icons(self):
        self.assertLess(len(self.window.icons.cache), 100, 'Laying out closed item pickers decodes the whole icon archive')

    def test_switching_full_storage_records_does_not_reload_item_choices(self):
        from native_ui import combo_options
        models = {key: control.model() for key, control in self.window.inventory_form.controls.items() if hasattr(control, 'model')}
        with patch('native_ui.combo_options', wraps=combo_options) as populate, patch.object(self.window.backend, 'call', wraps=self.window.backend.call) as read:
            started = time.perf_counter()
            self.window.inventory_slot = 1
            self.window.render_inventory()
            elapsed = time.perf_counter() - started
        catalog_rows = sum(len(call.args[1]) for call in populate.call_args_list if isinstance(call.args[1], list) and len(call.args[1]) > 100)
        print(f'Full-storage selection: {elapsed:.3f}s; catalog rows rebuilt: {catalog_rows}')
        self.assertEqual(catalog_rows, 0, 'Changing one saved item rebuilds thousands of unrelated picker choices')
        self.assertEqual(models, {key: control.model() for key, control in self.window.inventory_form.controls.items() if hasattr(control, 'model')})
        self.assertFalse(any(call.args[0] in ('inventory', 'items') for call in read.call_args_list), 'Selecting a slot reloads the unchanged storage/catalog')
        self.assertIs(models['upgrade0'], models['upgrade8'])
        self.assertEqual(self.window.backend.call('working'), list(self.original))

    def test_grid_preserves_slot_identity_and_invalid_drafts_when_filtering_or_selecting(self):
        from PySide6.QtCore import Qt
        form = self.window.inventory_form
        self.assertEqual(self.window.inventory_model.rowCount(), 990)
        self.assertEqual(self.window.inventory_grid.iconSize().width(), 40)
        form.write('quantity', 'abc'); form.track('quantity')
        self.window.inventory_grid.setCurrentIndex(self.window.inventory_model.index(5))
        self.assertEqual(self.window.inventory_slot, 0)
        self.assertEqual(self.window.inventory_grid.currentIndex().data(Qt.ItemDataRole.UserRole), 0)
        self.assertEqual(form.drafts, {'quantity': 'abc'})
        self.window.inventory_search.setText('990')
        self.assertEqual(self.window.inventory_model.rowCount(), 1)
        self.assertEqual(self.window.inventory_model.index(0).data(Qt.ItemDataRole.UserRole), 989)
        self.assertEqual(self.window.inventory_slot, 0)
        self.assertEqual(form.controls['quantity'].text(), 'abc')
        self.window.inventory_search.clear()
        form.clear()
        self.assertEqual(self.window.backend.call('working'), list(self.original))

    def test_valid_grid_selection_applies_to_the_old_slot_and_undo_refreshes_rows(self):
        form = self.window.inventory_form
        form.write('quantity', 8); form.track('quantity')
        self.window.inventory_grid.setCurrentIndex(self.window.inventory_model.index(1))
        self.assertEqual(self.window.inventory_slot, 1)
        self.assertEqual(self.window.backend.call('item', container='fridge', slot=0)['quantity'], 8)
        self.assertEqual(self.window.backend.call('item', container='fridge', slot=1)['quantity'], 9)
        self.assertFalse(form.drafts)
        self.window.mutate('undo')
        self.assertEqual(self.window.inventory_model.rows[0]['quantity'], 9)
        self.assertEqual(self.window.backend.call('working'), list(self.original))

    def test_item_search_popup_selects_the_matching_saved_id_without_writing(self):
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        self.window.container_combo.setCurrentIndex(self.window.container_combo.findData('bag'))
        control = self.window.inventory_form.controls['id']
        self.window.stack.currentWidget().ensureWidgetVisible(control)
        self.app.processEvents()
        control.setFocus(); control.lineEdit().selectAll()
        QTest.keyClicks(control.lineEdit(), 'Turnip Seeds')
        self.app.processEvents()
        popup = control.completer().popup()
        self.assertTrue(popup.isVisible())
        matches = popup.model().match(popup.model().index(0, 0), Qt.ItemDataRole.UserRole, 753, 1, Qt.MatchFlag.MatchExactly)
        self.assertEqual(len(matches), 1)
        index = matches[0]
        QTest.mouseClick(popup.viewport(), Qt.MouseButton.LeftButton, pos=popup.visualRect(index).center())
        self.assertEqual(control.currentData(), 753)
        self.assertEqual(self.window.backend.call('working'), list(self.original))
        self.window.inventory_form.clear()

    def test_language_changes_keep_drafts_and_retire_old_catalog_models(self):
        from PySide6.QtCore import QEvent
        from native_ui import _ItemChoices
        if self.window.language_combo.findData('zh-Hans') < 0: self.skipTest('Prepare bundled language names first')
        form = self.window.inventory_form
        form.write('quantity', 7); form.track('quantity')
        for code in ('zh-Hans', 'en'):
            self.window.language_combo.setCurrentIndex(self.window.language_combo.findData(code))
            self.assertEqual(form.drafts, {'quantity': '7'})
            self.assertEqual(form.controls['id'].currentData(), 753)
            self.assertEqual(self.window.backend.call('working'), list(self.original))
            self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            self.assertEqual(len(self.window.findChildren(_ItemChoices)), 3)
        form.clear()

    def test_unrecognized_saved_id_and_unmatched_search_text_are_preserved(self):
        data = bytearray(self.original)
        offset = self.window.constants['inventories']['fridge']['offset']
        struct.pack_into('<H', data, offset, 1777 | (1 << 11))
        struct.pack_into('<I', data, 0, zlib.crc32(data[4:-224]))
        self.window.open_bytes(data, 'synthetic.sav')
        self.window.container_combo.setCurrentIndex(self.window.container_combo.findData('fridge'))
        form = self.window.inventory_form
        self.assertEqual(form.controls['id'].currentData(), 1777)
        form.controls['id'].setEditText('not a matching item'); form.track('id')
        self.window.render_inventory()
        self.assertEqual(form.controls['id'].currentText(), 'not a matching item')
        with self.assertRaises(ValueError): form.changes()
        self.assertEqual(self.window.backend.call('working'), list(data))
        form.clear()
