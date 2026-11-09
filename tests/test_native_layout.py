"""Actual Qt layout regressions, using synthetic references and save bytes only."""
import ctypes
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = importlib.util.find_spec('PySide6') is not None and (ROOT / 'web/native-bundle.js').is_file()


@unittest.skipUnless(AVAILABLE, 'Native build dependencies / compiled core are not installed')
class NativeLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name == 'nt': ctypes.WinDLL(str(Path(os.environ['SystemRoot']) / 'System32' / 'icuuc.dll'))
        else: os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from native_ui import NativeWindow
        with patch('native_ui.local_references', return_value={}), patch('native_ui.QSettings') as settings:
            settings.return_value.value.return_value = 'en'
            self.window = NativeWindow()
        records = [{'category': 51, 'max_stack': 9} for _ in range(1024)]
        records[328] = {'category': 15, 'max_stack': 1}
        self.window.load_references({'items': {'tables': {'item': {'count': 1024, 'records': records}}}})
        self.window.open_bytes(bytes(self.window.backend.call('demoBytes')), 'synthetic.sav')
        self.window.ui_language_combo.setCurrentIndex(self.window.ui_language_combo.findData('zh-CN'))
        self.window.show()

    def tearDown(self):
        self.window.closing = True
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def settle(self):
        # Drain Qt's queued layout requests, without time-based sleeps.
        for _ in range(4): self.app.processEvents()

    def test_compact_chinese_inventory_does_not_require_horizontal_scrolling(self):
        self.window.resize(640, 480)
        self.window.navigation.setCurrentRow(self.window.pages['inventory'][2])
        self.settle()
        self.assertLessEqual(self.window.width(), 640, 'The window cannot shrink to a compact width')
        scroll = self.window.stack.currentWidget()
        self.assertEqual(scroll.horizontalScrollBar().maximum(), 0,
                         f'Inventory needs {scroll.horizontalScrollBar().maximum()}px horizontal scrolling at 640×480')

    def test_larger_chinese_font_fits_without_horizontal_overflow(self):
        font = self.window.font(); font.setPointSize(14); self.window.setFont(font)
        self.window.resize(850, 600)
        self.window.navigation.setCurrentRow(self.window.pages['inventory'][2])
        self.settle()
        self.assertLessEqual(self.window.width(), 850)
        scroll = self.window.stack.currentWidget()
        self.assertEqual(scroll.horizontalScrollBar().maximum(), 0,
                         f'Larger Chinese text overflows horizontally by {scroll.horizontalScrollBar().maximum()}px')

    def test_compact_chinese_field_labels_fit_their_allocated_rectangles(self):
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QLabel
        self.window.navigation.setCurrentRow(self.window.pages['inventory'][2])
        for points in (9, 14):
            font = self.window.font(); font.setPointSize(points); self.window.setFont(font)
            for width in (640, 850, 1250):
                with self.subTest(points=points, width=width):
                    self.window.resize(width, 600)
                    self.settle()
                    self.assertLessEqual(self.window.width(), width)
                    clipped = []
                    for label in self.window.inventory_form.body.findChildren(QLabel):
                        flags = Qt.TextFlag.TextWordWrap if label.wordWrap() else Qt.TextFlag.TextSingleLine
                        needed = label.fontMetrics().boundingRect(label.contentsRect(), int(flags), label.text())
                        if needed.width() > label.contentsRect().width() or needed.height() > label.contentsRect().height():
                            clipped.append((label.text(), label.width(), needed.width(), label.height(), needed.height()))
                    self.assertEqual(clipped, [], 'Chinese field labels are clipped: (text, actual width, needed width, actual height, needed height)')

    def test_compact_pages_fit_and_the_apply_button_is_reachable_by_vertical_scroll(self):
        for points, width in [(9, 640), (14, 850)]:
            font = self.window.font(); font.setPointSize(points); self.window.setFont(font)
            self.window.resize(width, 480)
            for page in ['overview', 'calendar', 'player', 'player-name', 'inventory', 'skills', 'recipes', 'friendship', 'relationships', 'people', 'trophies', 'marriage', 'flags', 'raw', 'reference', 'review']:
                with self.subTest(page=page, points=points):
                    self.window.navigation.setCurrentRow(self.window.pages[page][2])
                    self.settle()
                    scroll = self.window.stack.currentWidget()
                    self.assertEqual(scroll.horizontalScrollBar().maximum(), 0, f'{page} overflows horizontally')
        self.window.navigation.setCurrentRow(self.window.pages['inventory'][2])
        self.window.inventory_form.allow.setChecked(True)
        scroll = self.window.stack.currentWidget()
        self.settle()
        scroll.ensureWidgetVisible(self.window.inventory_form.apply_button)
        self.settle()
        button = self.window.inventory_form.apply_button
        from PySide6.QtCore import QPoint
        rect = button.rect().translated(button.mapTo(scroll.viewport(), QPoint(0, 0)))
        self.assertTrue(scroll.viewport().rect().contains(rect), 'Apply button is clipped/unreachable at the bottom of the form')

    def test_resizing_and_language_switching_keep_the_same_controls_and_disabled_drafts(self):
        self.window.navigation.setCurrentRow(self.window.pages['inventory'][2])
        form = self.window.inventory_form
        form.allow.setChecked(True); form.write('quantity', 'abc'); form.track('quantity'); form.allow.setChecked(False)
        controls, drafts, working = dict(form.controls), dict(form.drafts), self.window.backend.call('working')
        for width, language in [(640, 'en'), (1250, 'zh-CN'), (850, 'en'), (640, 'zh-CN')]:
            self.window.resize(width, 480)
            self.window.ui_language_combo.setCurrentIndex(self.window.ui_language_combo.findData(language))
            self.settle()
            self.assertEqual(form.controls, controls)
            self.assertEqual(form.controls['quantity'].text(), 'abc')
            self.assertEqual(form.drafts, drafts)
            self.assertEqual(self.window.backend.call('working'), working)

    def test_preview_tabs_are_translated_and_collapse_without_changing_the_save(self):
        self.window.navigation.setCurrentRow(self.window.pages['inventory'][2])
        tabs = self.window.item_preview_tabs
        self.assertEqual([tabs.tabText(index) for index in range(tabs.count())], ['当前物品', '草稿结果'])
        before = self.window.backend.call('working')
        tabs.parentWidget().setChecked(False)
        self.assertTrue(tabs.isHidden())
        tabs.parentWidget().setChecked(True)
        self.assertFalse(tabs.isHidden())
        self.assertEqual(self.window.backend.call('working'), before)

    def test_both_language_selectors_remain_visible_in_compact_windows(self):
        for points in (9, 14):
            font = self.window.font(); font.setPointSize(points); self.window.setFont(font)
            self.window.resize(640, 480)
            self.settle()
            for combo in (self.window.ui_language_combo, self.window.language_combo):
                self.assertTrue(combo.isVisibleTo(self.window), 'A language selector moved into an inaccessible toolbar overflow')
                self.assertGreaterEqual(combo.width(), 80)

    def test_relationship_pickers_preserve_drafts_across_languages_and_selection_guards(self):
        names = [''] * 186; names[24] = '＠しゅじんこうくん＠'; names[97] = 'Master'; names[133] = 'Vin'
        self.window.languages = {'en': {'label': 'English', 'nicknames': names}, 'zh-Hans': {'label': '简体中文', 'nicknames': list(names)}}
        self.window.languages['zh-Hans']['nicknames'][97] = '主人'
        self.window.update_languages()
        self.window.navigation.setCurrentRow(self.window.pages['relationships'][2])
        form, selector = self.window.record_forms['relationships'], self.window.record_selectors['relationships']
        self.assertEqual(selector.count(), 23)
        form.allow.setChecked(True)
        for field, value in [('dating', 1), ('npcCallsPlayer', 97), ('playerCallsNpc', 133)]: form.write(field, value); form.track(field)
        drafts, before = dict(form.drafts), self.window.backend.call('working')
        selector.setCurrentIndex(selector.findData(5))
        self.assertEqual(selector.currentData(), 1, 'Pending edits must stay attached to their NPC')
        form.allow.setChecked(False)
        for code in ['en', 'zh-CN']:
            self.window.ui_language_combo.setCurrentIndex(self.window.ui_language_combo.findData(code))
            self.assertEqual(form.drafts, drafts)
            self.assertEqual(form.controls['npcCallsPlayer'].currentData(), 97)
        self.window.language_combo.setCurrentIndex(self.window.language_combo.findData('zh-Hans'))
        self.assertIn('主人', form.controls['npcCallsPlayer'].currentText())
        self.assertEqual(form.drafts, drafts)
        self.assertEqual(self.window.backend.call('working'), before)
        self.assertFalse(self.window.export_action.isEnabled())
        form.allow.setChecked(True); form.apply_button.click()
        person = self.window.backend.call('relationships')[0]
        self.assertEqual((person['dating'], person['npcCallsPlayer'], person['playerCallsNpc']), (1, 97, 133))
        self.window.backend.call('undo'); self.assertEqual(self.window.backend.call('working'), before)

    def test_relationship_defaults_work_without_name_tables_and_non_candidates_cannot_date(self):
        self.window.backend.call('setNumber', offset=0x1db4c, type='u8', value=255)
        self.window.navigation.setCurrentRow(self.window.pages['relationships'][2])
        form, selector = self.window.record_forms['relationships'], self.window.record_selectors['relationships']
        self.assertEqual(form.controls['npcCallsPlayer'].currentData(), 255)
        self.assertIn('255', form.controls['npcCallsPlayer'].currentText())
        self.assertIn('rf3TxtHeroNickName', self.window.nickname_help.text())
        self.assertGreaterEqual(form.controls['npcCallsPlayer'].findData(24), 0)
        self.assertGreaterEqual(form.controls['npcCallsPlayer'].findData(71), 0)
        selector.setCurrentIndex(selector.findData(3)); form.allow.setChecked(True)
        self.assertFalse(form.controls['dating'].isEnabled())
        self.assertTrue(form.controls['npcCallsPlayer'].isEnabled())

    def test_player_name_edit_and_reset_are_drafts_with_unicode_and_record_guards(self):
        import struct, zlib
        data = bytearray(9304); data[:4] = b'RF4D'; struct.pack_into('<I', data, 8, 3)
        data[0x504:0x508] = b'Lest'; data[0x5a8:0x5ac] = b'Frey'
        struct.pack_into('<I', data, 4, zlib.crc32(data[8:]))
        self.window.open_bytes(data, 'rf4_sys.sav')
        self.window.navigation.setCurrentRow(self.window.pages['player-name'][2])
        form, selector = self.window.player_name_form, self.window.player_name_selector
        self.assertEqual(form.controls['name'].text(), 'Lest')
        self.assertFalse(self.window.reset_player_name_button.isEnabled())
        form.allow.setChecked(True); form.write('name', '芙蕾A'); form.track('name')
        selector.setCurrentIndex(selector.findData(1)); self.assertEqual(selector.currentData(), 0)
        form.allow.setChecked(False)
        self.window.ui_language_combo.setCurrentIndex(self.window.ui_language_combo.findData('en'))
        self.window.resize(640, 480); self.settle()
        self.assertEqual(form.controls['name'].text(), '芙蕾A')
        self.assertEqual(form.drafts, {'name': '芙蕾A'})
        self.assertFalse(self.window.export_action.isEnabled())
        self.assertEqual(self.window.backend.call('working'), list(data))
        form.allow.setChecked(True); form.apply_button.click()
        self.assertEqual(self.window.backend.call('playerNames')[0]['name'], '芙蕾A')
        before_reset = self.window.backend.call('working')
        self.window.reset_player_name_button.click()
        self.assertEqual(form.drafts, {'name': ''})
        self.assertEqual(self.window.backend.call('working'), before_reset)
        form.apply_button.click()
        self.assertTrue(self.window.backend.call('playerNames')[0]['usesDefault'])
        self.window.backend.call('undo'); self.assertEqual(self.window.backend.call('working'), before_reset)
        self.assertEqual(self.window.backend.call('original'), list(data))

    def test_name_page_explains_system_save_requirement_and_protects_empty_records(self):
        import struct, zlib
        self.window.navigation.setCurrentRow(self.window.pages['player-name'][2])
        self.assertIn('rf4_sys.sav', self.window.player_name_info.text())
        self.assertFalse(self.window.player_name_form.allow.isEnabled())
        data = bytearray(9304); data[:4] = b'RF4D'; struct.pack_into('<I', data, 4, zlib.crc32(data[8:]))
        self.window.open_bytes(data, 'rf4_sys.sav')
        self.assertFalse(self.window.player_name_form.allow.isEnabled())
        self.assertFalse(self.window.reset_player_name_button.isEnabled())


if __name__ == '__main__': unittest.main()
