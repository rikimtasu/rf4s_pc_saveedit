"""Shortcuts preserve drafts, byte boundaries, undo and compact localized forms."""
import ctypes
import importlib.util
import os
from pathlib import Path
import struct
import unittest
from unittest.mock import patch
import zlib

AVAILABLE = importlib.util.find_spec('PySide6') is not None


def item_references():
    records = [{'category': 51, 'max_stack': 9} for _ in range(1024)]
    for item_id, category in [(501, 24), (595, 33), (749, 37), (706, 35), (729, 36), (665, 34), (626, 34), (662, 34), (661, 34), (674, 34), (725, 36), (719, 36), (723, 36), (567, 28)]:
        records[item_id] = {'category': category, 'max_stack': 1}
    return {'items': {'tables': {'item': {'count': 1024, 'records': records},
        'equipment': {'count': 1024, 'records': [{'gear_params': 0} for _ in records]},
        'upgrade': {'count': 1024, 'records': [{'intelligence': 0} for _ in records]}}}}


@unittest.skipUnless(AVAILABLE, 'Native Qt dependencies are not installed')
class OrderSoilGearUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name == 'nt': ctypes.WinDLL(str(Path(os.environ['SystemRoot']) / 'System32' / 'icuuc.dll'))
        else: os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from native_ui import NativeWindow
        with patch('native_ui.QSettings') as settings, patch('native_ui.local_references', return_value=item_references()):
            settings.return_value.value.return_value = 'en'
            self.window = NativeWindow()
        self.window.testing = True; self.window.test_errors = []
        self.original = bytes(self.window.backend.call('demoBytes'))
        self.window.open_bytes(self.original, 'synthetic.sav'); self.window.show()

    def tearDown(self):
        self.window.closing = True; self.window.close(); self.window.deleteLater(); self.app.processEvents()

    def select(self, key):
        self.window.navigation.setCurrentRow(self.window.pages[key][2])
        for _ in range(4): self.app.processEvents()

    def edit(self, form, key, value):
        form.write(key, value); form.track(key)

    def test_orders_draft_validation_translation_and_atomic_apply(self):
        self.select('orders'); form = self.window.orders_form
        self.edit(form, 'enemyLevel', 127); self.edit(form, 'noExp', 1)
        with self.assertRaises(ValueError): self.window.apply_all_drafts()
        self.assertEqual(bytes(self.window.backend.call('working')), self.original)
        drafts = dict(form.drafts)
        self.window.ui_language_combo.setCurrentIndex(self.window.ui_language_combo.findData('zh-CN'))
        self.assertEqual(form.drafts, drafts)
        self.edit(form, 'enemyLevel', 10); self.edit(form, 'appearance', 9999)
        self.window.apply_all_drafts()
        self.assertEqual(self.window.backend.call('orders')['enemyLevel'], 10)
        self.assertEqual(self.window.backend.state()['gender'], 'male')
        self.assertEqual(self.window.backend.state()['undo'], 1)
        self.window.mutate('undo'); self.assertEqual(bytes(self.window.backend.call('working')), self.original)

    def test_soil_maximum_stages_and_keeps_bulk_selection_until_apply(self):
        self.select('soil'); form = self.window.soil_form
        self.edit(form, 'all', 1)
        self.window.soil_max_button.click()
        self.assertEqual(form.value('all'), 1)
        self.assertEqual(bytes(self.window.backend.call('working')), self.original)
        maximum = self.window.soil_constants['maximum']
        for key, value in maximum.items(): self.assertEqual(int(form.value(key)), value)
        self.window.apply_all_drafts()
        for patch_id in range(18): self.assertEqual(self.window.backend.call('soil', farm=0, patch=patch_id)['values'], maximum)
        self.assertEqual(self.window.backend.state()['undo'], 1)
        self.window.mutate('undo'); self.assertEqual(bytes(self.window.backend.call('working')), self.original)

    def test_both_gear_buttons_apply_with_other_drafts_as_one_undo(self):
        for key in ('staff-balanced', 'staff-damage'):
            with self.subTest(preset=key):
                self.window.open_bytes(self.original, 'synthetic.sav')
                self.select('player'); self.edit(self.window.player_form, 'money', 1234)
                self.select('gear')
                self.assertFalse(self.window.gear_buttons[key].isEnabled())
                self.window.gear_consent.setChecked(True)
                self.assertTrue(self.window.gear_buttons[key].isEnabled())
                self.window.gear_buttons[key].click()
                self.assertEqual(self.window.test_errors, [])
                self.assertEqual(self.window.backend.call('player')['money'], 1234)
                ids = [item['id'] for item in self.window.backend.call('inventory', container='bag')]
                for item_id in (501, 595, 749, 706, 729, 665): self.assertIn(item_id, ids)
                self.assertFalse(self.window.pending()); self.assertFalse(self.window.gear_consent.isChecked())
                self.assertEqual(self.window.backend.state()['undo'], 1)
                output = self.window.backend.build()
                self.assertEqual(struct.unpack_from('<I', output)[0], zlib.crc32(output[4:-224]))
                self.window.mutate('undo'); self.assertEqual(bytes(self.window.backend.call('working')), self.original)

    def test_failed_gear_does_not_apply_or_discard_invalid_pending_edits(self):
        self.select('orders'); form = self.window.orders_form
        self.edit(form, 'enemyLevel', 127)
        self.select('gear'); self.window.gear_consent.setChecked(True)
        self.window.gear_buttons['staff-damage'].click()
        self.assertTrue(self.window.test_errors)
        self.assertEqual(form.value('enemyLevel'), '127'); self.assertTrue(form.drafts)
        self.assertEqual(bytes(self.window.backend.call('working')), self.original)
        self.assertEqual(self.window.backend.state()['undo'], 0)

    def test_compact_localized_pages_and_missing_reference_guards(self):
        self.window.ui_language_combo.setCurrentIndex(self.window.ui_language_combo.findData('zh-CN'))
        self.window.resize(640, 480)
        for key in ('orders', 'gear', 'soil'):
            self.select(key)
            self.assertEqual(self.window.stack.currentWidget().horizontalScrollBar().maximum(), 0, key)
        self.select('gear')
        self.assertEqual(self.window.gear_buttons['staff-damage'].text(), '给予最大伤害法杖装备')
        self.window.load_references({}); self.window.gear_consent.setChecked(True); self.window.refresh()
        self.assertFalse(any(button.isEnabled() for button in self.window.gear_buttons.values()))
        self.assertEqual(bytes(self.window.backend.call('working')), self.original)

    def test_system_unlock_shortcut_stages_only_bit_zero_and_slot_tools_are_disabled(self):
        system = bytearray(9304); system[:4] = b'RF4D'
        struct.pack_into('<I', system, 8, 3); struct.pack_into('<I', system, 4, zlib.crc32(system[8:]))
        self.window.open_bytes(system, 'rf4_sys.sav'); self.select('system')
        self.window.extra_orders_unlock_button.click()
        self.assertEqual(self.window.system_form.drafts, {'0': 1})
        self.assertEqual(bytes(self.window.backend.call('working')), bytes(system))
        self.window.apply_all_drafts()
        output = self.window.backend.build()
        self.assertEqual(output[16], 1); self.assertEqual(output[8:16], system[8:16])
        self.window.render_orders(); self.window.render_soil(); self.window.render_gear_shortcuts()
        self.assertFalse(self.window.orders_form.allow.isEnabled()); self.assertFalse(self.window.soil_max_button.isEnabled())
        self.assertFalse(any(button.isEnabled() for button in self.window.gear_buttons.values()))
