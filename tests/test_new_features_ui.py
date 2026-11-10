"""New native editors use the existing draft/atomic-export lifecycle."""
import ctypes
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = importlib.util.find_spec('PySide6') is not None


@unittest.skipUnless(AVAILABLE, 'Native Qt build dependencies are not installed')
class NewFeaturesUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name == 'nt': ctypes.WinDLL(str(Path(os.environ['SystemRoot']) / 'System32' / 'icuuc.dll'))
        else: os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from native_ui import NativeWindow
        with patch('native_ui.QSettings') as settings, patch('native_ui.local_references', return_value={}):
            settings.return_value.value.return_value = 'en'
            self.window = NativeWindow()
        self.window.testing = True; self.window.test_errors = []
        self.original = bytes(self.window.backend.call('demoBytes'))
        self.window.open_bytes(self.original, 'synthetic.sav')
        self.window.show()

    def tearDown(self):
        self.window.closing = True; self.window.close(); self.window.deleteLater(); self.app.processEvents()

    def select(self, key):
        self.window.navigation.setCurrentRow(self.window.pages[key][2])
        for _ in range(4): self.app.processEvents()

    def edit(self, form, key, value):
        form.write(key, value); form.track(key)

    def test_endgame_button_stages_three_flags_without_applying_or_losing_drafts(self):
        self.select('flags'); form = self.window.story_form
        self.window.endgame_button.click()
        self.assertEqual(form.value('target'), '511')
        self.assertIn('FLG_SYELZA_ERACE', form.value('flags'))
        self.assertFalse(form.value('acknowledgeRisk'))
        self.assertEqual(bytes(self.window.backend.call('working')), self.original)
        with self.assertRaises(ValueError): self.window.apply_form(form, form.apply_callback)
        self.window.endgame_button.click()
        self.assertTrue(self.window.test_errors)
        self.assertEqual(form.value('target'), '511')
        self.edit(form, 'acknowledgeRisk', 1)
        self.window.apply_form(form, form.apply_callback)
        self.assertEqual(self.window.backend.state()['undo'], 1)
        self.window.mutate('undo'); self.assertEqual(bytes(self.window.backend.call('working')), self.original)

    def test_soil_health_bulk_edit_and_invalid_patch_switch_keep_the_correct_record(self):
        self.select('soil'); form = self.window.soil_form
        self.edit(form, 'health', 'invalid')
        self.window.soil_farm.setCurrentIndex(1)
        self.assertEqual(self.window.soil_location, (0, 0))
        self.assertEqual(self.window.soil_farm.currentData(), 0)
        self.assertEqual(form.value('health'), 'invalid')
        self.edit(form, 'health', 255); self.edit(form, 'all', 1)
        self.window.apply_form(form, form.apply_callback)
        for patch_id in range(18): self.assertEqual(self.window.backend.call('soil', farm=0, patch=patch_id)['values']['health'], 255)
        self.assertEqual(self.window.backend.state()['undo'], 1)
        self.window.mutate('undo'); self.assertEqual(bytes(self.window.backend.call('working')), self.original)

    def test_non_candidate_relationships_require_explicit_consent_and_preserve_other_records(self):
        self.select('relationships')
        self.window.record_selectors['relationships'].setCurrentIndex(2) # Volkanon
        form = self.window.record_forms['relationships']
        self.assertFalse(form.controls['dating'].isEnabled())
        self.edit(form, 'experimental', 1); self.assertTrue(form.controls['dating'].isEnabled())
        self.edit(form, 'dating', 1); self.window.apply_form(form, form.apply_callback)
        self.assertEqual(self.window.backend.call('relationships')[2]['dating'], 1)
        self.assertFalse(form.value('experimental'))
        self.select('marriage'); form = self.window.marriage_form
        self.edit(form, 'spouse', 21)
        with self.assertRaises(ValueError): self.window.apply_form(form, form.apply_callback)
        self.edit(form, 'experimental', 1); self.window.apply_form(form, form.apply_callback)
        self.assertEqual(self.window.backend.call('marriage', candidate=1)['spouse'], 21)
        self.window.mutate('undo'); self.window.mutate('undo')
        self.assertEqual(bytes(self.window.backend.call('working')), self.original)

    def test_roster_creation_respects_built_room_capacity_and_is_undoable(self):
        self.select('roster')
        self.assertFalse(self.window.roster_form.allow.isEnabled())
        self.window.backend.call('setFlag', name='REG_MON_HOUSE0_L_LV', value=1)
        self.window.refresh()
        form = self.window.roster_form
        self.assertTrue(form.allow.isEnabled())
        self.edit(form, 'species', 3); self.edit(form, 'name', '沃尔卡农')
        with self.assertRaises(ValueError): self.window.apply_form(form, form.apply_callback)
        self.edit(form, 'acknowledgeRisk', 1)
        self.window.apply_form(form, form.apply_callback)
        record = self.window.backend.call('monsters')[0]
        self.assertEqual(record['species'], 3); self.assertEqual(record['name'], '沃尔卡农')
        self.assertFalse(form.value('acknowledgeRisk'))
        self.assertEqual(form.value('slot'), 1)
        self.window.mutate('undo'); self.assertEqual(self.window.backend.call('monsters'), [])

    def test_new_pages_fit_compact_chinese_and_language_changes_preserve_soil_draft(self):
        self.window.ui_language_combo.setCurrentIndex(self.window.ui_language_combo.findData('zh-CN'))
        self.window.resize(640, 480)
        for key in ['soil', 'roster', 'flags', 'marriage']:
            self.select(key)
            self.assertEqual(self.window.stack.currentWidget().horizontalScrollBar().maximum(), 0, key)
        self.select('soil'); self.edit(self.window.soil_form, 'health', 123)
        drafts = dict(self.window.soil_form.drafts)
        self.window.ui_language_combo.setCurrentIndex(self.window.ui_language_combo.findData('en'))
        self.assertEqual(self.window.soil_form.drafts, drafts)
        self.assertEqual(bytes(self.window.backend.call('working')), self.original)

    def test_nickname_reset_buttons_stage_each_direction_or_both_for_current_gender(self):
        for code, gender, expected in [(0, 'male', (24, 1)), (1, 'female', (71, 48))]:
            with self.subTest(gender=gender):
                self.window.open_bytes(self.original, 'synthetic.sav')
                self.window.backend.call('setNumber', offset=0x36, type='u8', value=code)
                self.window.backend.call('setRelationship', id=1, changes={'dating': 1, 'npcCallsPlayer': 97, 'playerCallsNpc': 133})
                self.window.refresh()
                self.select('relationships'); form = self.window.record_forms['relationships']
                before, state = self.window.backend.call('working'), self.window.backend.state()
                self.window.nickname_reset_buttons['npcCallsPlayer'].click()
                self.assertEqual(form.value('npcCallsPlayer'), expected[0]); self.assertEqual(form.value('playerCallsNpc'), 133)
                self.assertEqual(form.drafts, {'npcCallsPlayer': expected[0]})
                form.clear()
                self.window.nickname_reset_buttons['playerCallsNpc'].click()
                self.assertEqual(form.value('npcCallsPlayer'), 97); self.assertEqual(form.value('playerCallsNpc'), expected[1])
                form.clear()
                self.window.nickname_reset_buttons['both'].click()
                self.assertEqual(form.drafts, {'npcCallsPlayer': expected[0], 'playerCallsNpc': expected[1]})
                self.assertEqual(self.window.backend.call('working'), before); self.assertEqual(self.window.backend.state(), state)
                self.window.apply_form(form, form.apply_callback)
                record = self.window.backend.call('relationships')[0]
                self.assertEqual((record['npcCallsPlayer'], record['playerCallsNpc']), expected)
                self.assertEqual(record['dating'], 1)
                self.assertEqual(self.window.backend.state()['undo'], state['undo'] + 1)
                self.window.mutate('undo'); self.assertEqual(self.window.backend.call('working'), before)

    def test_nickname_reset_preserves_other_drafts_and_survives_language_changes(self):
        self.select('relationships')
        self.window.record_selectors['relationships'].setCurrentIndex(2)
        form = self.window.record_forms['relationships']
        self.edit(form, 'experimental', 1); self.edit(form, 'dating', 1)
        self.window.nickname_reset_buttons['both'].click()
        self.assertEqual(form.drafts['experimental'], 1); self.assertEqual(form.drafts['dating'], 1)
        self.assertEqual(form.value('npcCallsPlayer'), 26); self.assertEqual(form.value('playerCallsNpc'), 3)
        drafts = dict(form.drafts)
        self.window.ui_language_combo.setCurrentIndex(self.window.ui_language_combo.findData('zh-CN'))
        self.assertIn('Lest', self.window.nickname_reset_target.text())
        self.assertEqual(self.window.nickname_reset_buttons['both'].text(), '按当前性别重置双方称呼')
        self.assertEqual(form.drafts, drafts)
        self.assertEqual(bytes(self.window.backend.call('working')), self.original)
        self.window.backend.call('setNumber', offset=0x36, type='u8', value=1); self.window.refresh()
        self.window.nickname_reset_buttons['both'].click()
        self.assertEqual(form.value('npcCallsPlayer'), 73); self.assertEqual(form.value('playerCallsNpc'), 50)
        self.assertEqual(form.drafts['dating'], 1)

    def test_nickname_reset_rejects_unknown_gender_and_disabled_forms_without_losing_drafts(self):
        self.select('relationships'); form = self.window.record_forms['relationships']
        self.edit(form, 'npcCallsPlayer', 71)
        self.window.backend.call('setNumber', offset=0x36, type='u8', value=2); self.window.refresh()
        self.assertFalse(any(button.isEnabled() for button in self.window.nickname_reset_buttons.values()))
        drafts, before = dict(form.drafts), self.window.backend.call('working')
        with self.assertRaises(ValueError): self.window.reset_nickname_draft()
        self.assertEqual(form.drafts, drafts); self.assertEqual(self.window.backend.call('working'), before)
        self.window.backend.call('undo'); self.window.refresh()
        form.allow.setChecked(False)
        self.assertFalse(any(button.isEnabled() for button in self.window.nickname_reset_buttons.values()))
        with self.assertRaises(ValueError): self.window.reset_nickname_draft()
        self.assertEqual(form.drafts, drafts)


if __name__ == '__main__': unittest.main()
