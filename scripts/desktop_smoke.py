"""Test actual native Qt controls and an exported synthetic save, never a personal save."""
import json
from pathlib import Path
import struct
import zlib
from unittest.mock import patch

from PySide6.QtCore import QTimer, QCoreApplication
from PySide6.QtWidgets import QMessageBox
from scripts.game_sources import all_references


def run(app, window, destination, game=None):
    output = Path(destination)
    output.mkdir(parents=True, exist_ok=True)
    window.testing = True
    window.test_errors = []

    def select_page(key):
        window.navigation.setCurrentRow(window.pages[key][2])

    def edit(form, key, value):
        form.write(key, value)
        form.track(key)

    def check_discard_dialog(code):
        captured = {}

        def inspect():
            dialog = app.activeModalWidget()
            if isinstance(dialog, QMessageBox):
                captured['captions'] = [dialog.button(button).text().replace('&', '') for button in
                                       (QMessageBox.StandardButton.Discard, QMessageBox.StandardButton.Cancel)]
                captured['default'] = dialog.defaultButton() == dialog.button(QMessageBox.StandardButton.Cancel)
                captured['width'] = dialog.width()
                dialog.grab().save(str(output / f'desktop-discard-{code}.png'))
                dialog.button(QMessageBox.StandardButton.Cancel).click()
            elif dialog: dialog.reject()

        QTimer.singleShot(0, inspect)
        accepted = window.discard_confirmation()
        expected = ['放弃', '取消'] if code == 'zh-CN' else ['Discard', 'Cancel']
        return not accepted and captured.get('captions') == expected and captured.get('default') and captured.get('width', 0) >= 360

    def exercise():
        checks = {}
        try:
            if game: window.load_references(all_references(game))
            original = bytes(window.backend.call('demoBytes'))
            window.open_bytes(original, 'synthetic.sav')
            appdata = output / 'appdata'; save_folder = appdata / 'Rune Factory 4 Special'; save_folder.mkdir(parents=True, exist_ok=True)
            with patch.dict('os.environ', {'APPDATA': str(appdata.resolve())}), patch('native_ui.QFileDialog.getOpenFileName', return_value=('', '')) as picker:
                window.open_file()
                checks['defaultSavePicker'] = Path(picker.call_args.args[2]) == save_folder.resolve() and bytes(window.backend.call('original')) == original
            select_page('inventory')
            form = window.inventory_form
            form.allow.setChecked(True)
            edit(form, 'craft0', 839)
            edit(form, 'element', 1)
            checks['itemDraftGuard'] = window.pending() and not window.export_action.isEnabled()
            saved_mode = window.ui_language_mode
            draft = dict(form.drafts); working = window.backend.call('working'); game_language = window.language
            window.ui_language_combo.setCurrentIndex(window.ui_language_combo.findData('zh-CN'))
            checks['chineseInterface'] = form.allow.text() == '启用编辑' and window.export_action.text() == '导出修改后的存档'
            checks['chineseDraftPreservation'] = form.drafts == draft and window.backend.call('working') == working and window.language == game_language
            checks['chineseStandardButtons'] = QCoreApplication.translate('QPlatformTheme', 'Cancel') == '取消'
            checks['chineseDiscardDialog'] = check_discard_dialog('zh-CN')
            checks['itemEffectPreview'] = '草稿结果' in window.item_preview_after.toPlainText() and '基于定义' in window.item_preview_after.toPlainText()
            window.grab().save(str(output / 'desktop-chinese-preview.png'))
            compact_ok = True
            for width, height in [(640, 480), (850, 600), (1250, 850)]:
                window.resize(width, height)
                for _ in range(4): app.processEvents()
                compact_ok = compact_ok and window.width() <= width and window.stack.currentWidget().horizontalScrollBar().maximum() == 0
            checks['responsiveChineseLayout'] = compact_ok
            window.resize(640, 480)
            window.item_preview_tabs.parentWidget().setChecked(False)
            for _ in range(4): app.processEvents()
            window.stack.currentWidget().ensureWidgetVisible(form.apply_button)
            for _ in range(4): app.processEvents()
            window.grab().save(str(output / 'desktop-chinese-compact.png'))
            window.item_preview_tabs.parentWidget().setChecked(True)
            window.resize(1160, 850)
            window.stack.currentWidget().verticalScrollBar().setValue(0)
            edit(form, 'quantity', 'abc'); form.allow.setChecked(False)
            typed = dict(form.drafts)
            window.ui_language_combo.setCurrentIndex(window.ui_language_combo.findData('en'))
            checks['typedDisabledDraftPreservation'] = form.controls['quantity'].text() == 'abc' and form.drafts == typed and window.backend.call('working') == working
            checks['englishDiscardDialog'] = check_discard_dialog('en')
            form.allow.setChecked(True); form.write('quantity', 1); form.track('quantity')
            window.ui_language_combo.setCurrentIndex(window.ui_language_combo.findData(saved_mode))
            window.container_combo.setCurrentIndex(window.container_combo.findData('fridge'))
            checks['containerDraftGuard'] = window.inventory_container == 'bag' and window.container_combo.currentData() == 'bag'
            form.apply_button.click()
            item = window.backend.call('item', container='bag', slot=0)
            checks['attachments'] = item['details']['craft0'] == 839 and item['level'] == 3
            checks['element'] = item['element'] == 1
            select_page('marriage')
            form = window.marriage_form
            form.allow.setChecked(True)
            edit(form, 'spouse', 17)
            checks['marriageDraftGuard'] = window.pending() and not window.export_action.isEnabled()
            form.allow.setChecked(False)
            checks['disabledDraftGuard'] = window.pending() and not window.export_action.isEnabled()
            form.allow.setChecked(True)
            form.apply_button.click()
            checks['spouse'] = window.backend.call('marriage', candidate=1)['spouse'] == 17
            select_page('friendship')
            form = window.record_forms['friendship']; selector = window.record_selectors['friendship']
            targets = {npc: npc * 13 for npc in range(1, 24)}
            targets.update({24: 10, 25: 27})
            for npc, level in targets.items():
                selector.setCurrentIndex(selector.findData(npc))
                form.allow.setChecked(True)
                edit(form, 'level', level); form.apply_button.click()
            checks['allFriendshipControls'] = all(person['level'] == targets[person['id']] for person in window.backend.call('friendship'))
            select_page('relationships')
            selector = window.record_selectors['relationships']; selector.setCurrentIndex(selector.findData(2))
            form = window.record_forms['relationships']; form.allow.setChecked(True)
            edit(form, 'dating', 1); edit(form, 'npcCallsPlayer', 94); edit(form, 'playerCallsNpc', 136)
            checks['relationshipDraftGuard'] = window.pending() and not window.export_action.isEnabled()
            form.apply_button.click()
            person = window.backend.call('relationships')[1]
            checks['datingAndNicknameControls'] = (person['dating'], person['npcCallsPlayer'], person['playerCallsNpc']) == (1, 94, 136)
            checks['nicknameGameTables'] = len(window.nickname_names()) == 186 and selector.count() == 23
            window.grab().save(str(output / 'desktop-relationships.png'))
            select_page('player')
            form = window.player_form; form.allow.setChecked(True)
            edit(form, 'money', '1234'); form.apply_button.click()
            checks['sevenLanguages'] = window.language_combo.count() == 7
            window.language_combo.setCurrentIndex(window.language_combo.findData('zh-Hans'))
            checks['localizedNames'] = window.item_name(1) == '卷心菜'
            for key in ['calendar', 'player-name', 'skills', 'recipes', 'friendship', 'relationships', 'people', 'monsters', 'trophies', 'flags', 'raw', 'reference', 'review']:
                select_page(key)
            checks['allNativePages'] = not window.test_errors
            checks['noDrafts'] = not window.pending()
            select_page('flags')
            window.flag_search.setText('主线剧情进度')
            checks['chineseFlagSearch'] = window.flag_selector.currentData() == 'REG_MAIN_SCENARIO'
            checks['flagImpactPreview'] = 'REG_MAIN_SCENARIO' in window.flag_impact.toPlainText()
            select_page('review')
            checks['datingCleanupOffByDefault'] = not window.reset_dating.isChecked()
            window.backend.call('setNumber', offset=0x1db48, type='u32', value=0x400302)
            window.backend.call('patchBytes', offset=0x1db4c, text='61')
            before_cleanup = bytes(window.backend.call('working'))
            window.export_gender.setCurrentIndex(window.export_gender.findData('male'))
            window.reset_dating.setChecked(True)
            checks['datingCleanupPreview'] = 'Vishnal' in window.dating_preview.text() and 'Leon' in window.dating_preview.text()
            exported = window.export_bytes()
            checks['datingCleanup'] = struct.unpack_from('<I', exported, 0x1db48)[0] == 0x302 and exported[0x1db4c] == 24
            checks['datingCleanupExportOnly'] = bytes(window.backend.call('working')) == before_cleanup
            checks['checksum'] = len(exported) == 140424 and struct.unpack_from('<I', exported)[0] == zlib.crc32(exported[4:-224])
            checks['money'] = struct.unpack_from('<i', exported, 0x4c)[0] == 1234
            checks['friendshipExportFields'] = all(struct.unpack_from('<i', exported, 0x1db40 + (npc - 1) * 44)[0] == level * 336 - 2015
                                                   for npc, level in targets.items() if npc < 24)
            checks['guestFriendshipExportFields'] = struct.unpack_from('<H', exported, 0x1df6c)[0] >> 2 == 10 and struct.unpack_from('<H', exported, 0x1df74)[0] >> 2 == 27
            clorica = 0x1db40 + 44
            checks['relationshipExportFields'] = bool(struct.unpack_from('<I', exported, clorica + 8)[0] & 0x400000) and exported[clorica + 12] == 94 and struct.unpack_from('<I', exported, clorica + 20)[0] >> 7 & 255 == 136
            checks['originalUnchanged'] = bytes(window.backend.call('original')) == original
            if not all(checks.values()): raise AssertionError(checks)
            window.write_file(output / 'synthetic.edited.sav', exported)
            window.last_export = bytes(window.backend.call('working'))
            select_page('inventory')
            window.grab().save(str(output / 'desktop.png'))
            system = bytearray(9304); system[:4] = b'RF4D'
            struct.pack_into('<I', system, 8, 3)
            system[0x504:0x508] = b'Lest'; system[0x5a8:0x5ac] = b'Frey'
            struct.pack_into('<I', system, 4, zlib.crc32(system[8:]))
            window.open_bytes(system, 'rf4_sys.sav')
            checks['datingCleanupResetsOnOpen'] = not window.reset_dating.isChecked()
            select_page('system')
            window.system_form.allow.setChecked(True)
            edit(window.system_form, '2', 1)
            window.system_form.apply_button.click()
            system_output = window.export_bytes()
            checks['systemNativeControls'] = struct.unpack_from('<I', system_output, 16)[0] == 4 and struct.unpack_from('<I', system_output, 8)[0] == 3 and struct.unpack_from('<I', system_output, 4)[0] == zlib.crc32(system_output[8:])
            select_page('player-name')
            window.ui_language_combo.setCurrentIndex(window.ui_language_combo.findData('zh-CN'))
            form = window.player_name_form; form.allow.setChecked(True)
            edit(form, 'name', '芙蕾A')
            checks['playerNameDraftGuard'] = window.pending() and not window.export_action.isEnabled()
            form.apply_button.click()
            named = window.export_bytes()
            checks['playerNameUnicode'] = named[0x504:0x517].split(b'\0')[0] == '芙蕾A'.encode('utf-8')
            window.write_file(output / 'synthetic.system-named.sav', named)
            before_reset = window.backend.call('working')
            window.reset_player_name_button.click()
            checks['playerNameResetDraft'] = form.drafts == {'name': ''} and window.backend.call('working') == before_reset and not window.export_action.isEnabled()
            form.apply_button.click()
            default_name = window.export_bytes()
            checks['playerNameReset'] = default_name[0x504:0x517] == bytes(19) and struct.unpack_from('<I', default_name, 8)[0] == 3
            checks['playerNameExportCrc'] = struct.unpack_from('<I', default_name, 4)[0] == zlib.crc32(default_name[8:])
            checks['systemOriginalUnchanged'] = bytes(window.backend.call('original')) == bytes(system)
            window.write_file(output / 'synthetic.system-default.sav', default_name)
            window.grab().save(str(output / 'desktop-player-name.png'))
            if not all(checks.values()) or window.test_errors: raise AssertionError((checks, window.test_errors))
            (output / 'desktop-test.json').write_text(json.dumps({'passed': True, 'native': True, 'checks': checks}, indent=2), encoding='utf-8')
            window.closing = True
            app.exit(0)
        except Exception as error:
            (output / 'desktop-test.json').write_text(json.dumps({'passed': False, 'detail': str(error), 'checks': checks}, indent=2), encoding='utf-8')
            window.closing = True
            app.exit(1)

    QTimer.singleShot(0, exercise)
