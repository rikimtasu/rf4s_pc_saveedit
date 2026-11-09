"""Exercise the standalone native workflow; never write a user's save folder."""
import json
from pathlib import Path
import struct
import tempfile
from unittest.mock import patch
import zlib

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QCheckBox, QPushButton
from native_save import local_references


def run(app, window, destination, game=None):
    output = Path(destination); output.mkdir(parents=True, exist_ok=True)
    window.testing = True; window.test_errors = []
    saved_mode = window.ui_language_mode

    def page(key): window.navigation.setCurrentRow(window.pages[key][2])
    def edit(form, key, value): form.write(key, value); form.track(key)
    def valid(data): return struct.unpack_from('<I', data, 4 if data[:4] == b'RF4D' else 0)[0] == zlib.crc32(data[8:] if data[:4] == b'RF4D' else data[4:-224])

    def exercise():
        checks = {}
        try:
            # No all_references(game), imports or game-directory picker: the
            # packaged catalog must provide the actual definitions and icons.
            original = bytes(window.backend.call('demoBytes'))
            window.open_bytes(original, 'rf4_s01.sav')
            checks['standaloneLanguages'] = window.language_combo.count() == 7 and len(window.nickname_names()) == 186
            references = local_references()
            expected_items = references['items']['tables']['item']['count'] - 1
            expected_recipes = sum(len(table['records']) for table in references['recipes']['recipes'])
            checks['standaloneDefinitions'] = len(window.backend.call('items')) == expected_items and len(window.backend.call('recipes')) == expected_recipes and expected_recipes > 0
            checks['noEditingOptIns'] = not any(button.text() in ('Enable editing', '启用编辑') for button in window.findChildren(QCheckBox))
            checks['noDemoButton'] = not any('synthetic' in button.text().lower() or '模拟存档' in button.text() for button in window.findChildren(QPushButton))
            page('player'); edit(window.player_form, 'tourists', '12345')
            page('inventory'); form = window.inventory_form
            edit(form, 'craft0', 839); edit(form, 'element', 1)
            checks['itemIcons'] = not form.controls['id'].itemIcon(form.controls['id'].findData(328)).isNull() and not window.icons.icon('items', 839).isNull()
            drafts = dict(form.drafts)
            window.ui_language_combo.setCurrentIndex(window.ui_language_combo.findData('zh-CN'))
            window.language_combo.setCurrentIndex(window.language_combo.findData('zh-Hans'))
            checks['chineseAndDrafts'] = form.drafts == drafts and window.item_name(1) == '卷心菜'
            window.resize(640, 480)
            for _ in range(4): app.processEvents()
            checks['compactLayout'] = window.width() == 640 and window.stack.currentWidget().horizontalScrollBar().maximum() == 0
            window.grab().save(str(output / 'desktop-items.png'))
            appdata = Path(tempfile.mkdtemp(prefix='appdata-', dir=output)); folder = appdata / 'Rune Factory 4 Special'; folder.mkdir(parents=True, exist_ok=True)
            target = folder / 'rf4_s01.sav'; target.write_bytes(original)
            with patch.dict('os.environ', {'APPDATA': str(appdata.resolve())}), patch('native_ui.QFileDialog.getSaveFileName', side_effect=AssertionError('Direct export must not open Save as')):
                window.export_file()
                edited = target.read_bytes()
                checks['automaticDraftExport'] = not window.pending() and struct.unpack_from('<i', edited, 0x20714)[0] == 12345
                checks['sameFolderBackup'] = next(folder.glob('rf4_s01.sav.backup-*.bak')).read_bytes() == original
                item = window.backend.call('item', container='bag', slot=0)
                checks['attachmentsAndElement'] = item['details']['craft0'] == 839 and item['element'] == 1
                checks['crcAndOriginal'] = valid(edited) and bytes(window.backend.call('original')) == original
                page('friendship'); selector = window.record_selectors['friendship']; form = window.record_forms['friendship']
                selector.setCurrentIndex(selector.findData(24)); edit(form, 'level', 27)
                selector.setCurrentIndex(selector.findData(25)); edit(form, 'level', 10)
                checks['recordAutoApply'] = window.backend.call('friendship')[23]['level'] == 27
                page('relationships'); selector = window.record_selectors['relationships']; selector.setCurrentIndex(selector.findData(2))
                checks['portraitIcons'] = not selector.itemIcon(selector.findData(2)).isNull()
                form = window.record_forms['relationships']; edit(form, 'dating', 1); edit(form, 'npcCallsPlayer', 94); edit(form, 'playerCallsNpc', 136)
                window.export_file(); edited = target.read_bytes()
                checks['guestFriendship'] = struct.unpack_from('<H', edited, 0x1df6c)[0] >> 2 == 27 and struct.unpack_from('<H', edited, 0x1df74)[0] >> 2 == 10
                person = window.backend.call('relationships')[1]
                checks['datingAndNicknames'] = (person['dating'], person['npcCallsPlayer'], person['playerCallsNpc']) == (1, 94, 136)
                window.write_file(output / 'synthetic.edited.sav', edited)
                system = bytearray(9304); system[:4] = b'RF4D'; struct.pack_into('<I', system, 8, 3)
                system[0x504:0x508] = b'Lest'; struct.pack_into('<I', system, 4, zlib.crc32(system[8:]))
                window.open_bytes(system, 'rf4_sys.sav')
                page('system'); edit(window.system_form, '5', 1)
                page('player-name'); edit(window.player_name_form, 'name', '芙蕾A')
                window.export_file(); named = (folder / 'rf4_sys.sav').read_bytes()
                checks['playerNameAndSystemFlags'] = named[0x504:0x517].split(b'\0')[0] == '芙蕾A'.encode('utf-8') and struct.unpack_from('<I', named, 16)[0] == 32 and struct.unpack_from('<I', named, 8)[0] == 3
                window.write_file(output / 'synthetic.system-named.sav', named)
                window.reset_player_name_button.click(); window.export_file()
                reset = (folder / 'rf4_sys.sav').read_bytes()
                checks['nameResetAndBackup'] = reset[0x504:0x517] == bytes(19) and len(list(folder.glob('rf4_sys.sav.backup-*.bak'))) == 2
                checks['systemCrcAndOriginal'] = valid(reset) and bytes(window.backend.call('original')) == bytes(system)
                window.write_file(output / 'synthetic.system-default.sav', reset)
                window.grab().save(str(output / 'desktop-player-name.png'))
            if not all(checks.values()) or window.test_errors: raise AssertionError((checks, window.test_errors))
            (output / 'desktop-test.json').write_text(json.dumps({'passed': True, 'native': True, 'checks': checks}, indent=2), encoding='utf-8')
            window.closing = True; app.exit(0)
        except Exception as error:
            (output / 'desktop-test.json').write_text(json.dumps({'passed': False, 'error': str(error), 'checks': checks}, indent=2), encoding='utf-8')
            window.closing = True; app.exit(1)
        finally:
            window.ui_language_combo.setCurrentIndex(window.ui_language_combo.findData(saved_mode))

    QTimer.singleShot(0, exercise)
