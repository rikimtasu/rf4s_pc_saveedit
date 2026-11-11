"""Exercise the standalone native workflow; never write a user's save folder."""
import json
from pathlib import Path
import struct
import tempfile
from unittest.mock import patch
import zlib

from PySide6.QtCore import QTimer
from PySide6.QtGui import QPalette, QTextLayout
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
            checks['notoMediumFont'] = window.font().families() == ['Noto Sans', 'Noto Sans CJK SC'] and window.font().weight() == 500
            layout = QTextLayout('English 中文 剧情编辑 繁體字', window.font())
            layout.beginLayout(); line = layout.createLine(); line.setLineWidth(1000); layout.endLayout()
            runs = layout.glyphRuns()
            checks['notoChineseAndEnglish'] = {run.rawFont().familyName() for run in runs} == {'Noto Sans', 'Noto Sans CJK SC'} and all(run.rawFont().weight() == 500 and 0 not in run.glyphIndexes() for run in runs)
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
                reset_before = window.backend.call('working')
                window.nickname_reset_buttons['both'].click()
                defaults = window.backend.call('relationshipDefaults', id=2)['defaults']
                checks['nicknameResetDraft'] = window.backend.call('working') == reset_before and form.value('npcCallsPlayer') == defaults['npcCallsPlayer'] and form.value('playerCallsNpc') == defaults['playerCallsNpc']
                window.apply_form(form, form.apply_callback)
                person = window.backend.call('relationships')[1]
                checks['nicknameResetPreservesDating'] = person['dating'] == 1 and all(person[key] == value for key, value in defaults.items())
                window.backend.call('undo'); window.refresh()
                checks['nicknameResetUndo'] = window.backend.call('working') == reset_before
                window.grab().save(str(output / 'desktop-nickname-reset.png'))
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
            window.open_bytes(original, 'rf4_s01.sav')
            page('recipes')
            popup = window.record_selectors['recipes'].view(); popup.ensurePolished()
            checks['nordPopupPalette'] = popup.palette().color(QPalette.ColorRole.Base).name() == '#2e3440' and popup.palette().color(QPalette.ColorRole.Text).name() == '#eceff4'
            window.learn_all_recipes_action.trigger()
            checks['learnAllRecipes'] = all(recipe['known'] for recipe in window.backend.call('recipes')) and window.backend.state()['undo'] == 1
            window.grab().save(str(output / 'desktop-recipes.png'))
            window.backend.call('undo')
            checks['learnAllUndo'] = bytes(window.backend.call('working')) == original
            checks['compactTypography'] = window.font().pointSize() == 11 and window.inventory_grid.gridSize().width() == 104 and window.inventory_form.controls['id'].iconSize().width() == 24
            window.resize(1000, 720)
            page('flags'); window.endgame_button.click()
            checks['endgameStagedOnly'] = window.story_form.value('target') == '511' and bytes(window.backend.call('working')) == original
            edit(window.story_form, 'acknowledgeRisk', 1)
            window.apply_form(window.story_form, window.story_form.apply_callback)
            checks['endgameApplied'] = window.backend.call('storyJumpPreview', target=511)['from'] == 511
            window.backend.call('undo')
            page('soil'); edit(window.soil_form, 'health', 255); edit(window.soil_form, 'all', 1)
            window.apply_form(window.soil_form, window.soil_form.apply_callback)
            checks['soilBulk'] = all(window.backend.call('soil', farm=0, patch=i)['values']['health'] == 255 for i in range(18))
            window.grab().save(str(output / 'desktop-soil.png'))
            window.backend.call('undo')
            page('relationships'); window.record_selectors['relationships'].setCurrentIndex(2)
            form = window.record_forms['relationships']; edit(form, 'experimental', 1); edit(form, 'dating', 1)
            window.apply_form(form, form.apply_callback)
            checks['experimentalDating'] = window.backend.call('relationships')[2]['dating'] == 1
            window.backend.call('undo')
            page('marriage'); edit(window.marriage_form, 'spouse', 21); edit(window.marriage_form, 'experimental', 1)
            window.apply_form(window.marriage_form, window.marriage_form.apply_callback)
            checks['experimentalSpouse'] = window.backend.call('marriage', candidate=1)['spouse'] == 21
            window.backend.call('undo')
            window.backend.call('setFlag', name='REG_MON_HOUSE0_L_LV', value=1)
            page('roster'); form = window.roster_form
            edit(form, 'species', 3); edit(form, 'name', '沃尔卡农'); edit(form, 'acknowledgeRisk', 1)
            window.apply_form(form, form.apply_callback)
            checks['experimentalRoster'] = window.backend.call('monsters')[0]['species'] == 3 and window.backend.call('roster')['housing'][0]['free'] == 3
            window.grab().save(str(output / 'desktop-roster.png'))
            window.backend.call('undo'); window.backend.call('undo')
            checks['newEditorsUndo'] = bytes(window.backend.call('working')) == original and not window.pending()
            page('orders'); form = window.orders_form
            edit(form, 'enemyLevel', 10); edit(form, 'noExp', 1); edit(form, 'showEnemyHp', 1)
            window.apply_all_drafts()
            values = window.backend.call('orders')
            checks['extraOrders'] = values['enemyLevel'] == 10 and values['noExp'] == 1 and values['showEnemyHp'] == 1 and valid(window.backend.build())
            window.grab().save(str(output / 'desktop-extra-orders.png'))
            window.backend.call('undo'); window.refresh()
            edit(window.orders_forms['licenses'], 'forgeLicense', 1)
            edit(window.orders_forms['shops'], 'nationalizeBaths', 1)
            edit(window.orders_forms['expansions'], 'bagExpansion', 1)
            edit(window.orders_forms['other'], 'everyoneSwimsuits', 1)
            edit(window.orders_forms['other'], 'princeRank', 17)
            window.apply_all_drafts()
            values = window.backend.call('orders')
            checks['extendedOrders'] = all(values[key] == value for key, value in {'forgeLicense': 1, 'nationalizeBaths': 1, 'bagExpansion': 1, 'everyoneSwimsuits': 1, 'princeRank': 17}.items()) and window.backend.state()['undo'] == 1 and valid(window.backend.build())
            for index in range(window.order_tabs.count()):
                window.order_tabs.setCurrentIndex(index)
                for _ in range(4): app.processEvents()
                checks[f'orderTab{index}Compact'] = window.stack.currentWidget().horizontalScrollBar().maximum() == 0
            window.grab().save(str(output / 'desktop-more-orders.png'))
            window.backend.call('undo'); window.refresh()
            page('soil'); window.soil_max_button.click(); edit(window.soil_form, 'all', 1)
            checks['maxSoilStaged'] = bytes(window.backend.call('working')) == original
            window.apply_all_drafts()
            checks['maxSoil'] = all(window.backend.call('soil', farm=0, patch=i)['values'] == window.soil_constants['maximum'] for i in range(18))
            window.backend.call('undo'); window.refresh()
            for key in ('staff-balanced', 'staff-damage'):
                page('gear'); window.gear_consent.setChecked(True); window.gear_buttons[key].click()
                ids = [item['id'] for item in window.backend.call('inventory', container='bag')]
                checks[key] = all(item_id in ids for item_id in (501, 595, 749, 706, 729, 665)) and window.backend.state()['undo'] == 1 and valid(window.backend.build())
                window.backend.call('undo'); window.refresh()
            window.resize(640, 480)
            for key in ('gear', 'orders', 'soil'):
                page(key)
                for _ in range(4): app.processEvents()
                checks[f'{key}ShortcutCompact'] = window.stack.currentWidget().horizontalScrollBar().maximum() == 0
            page('gear'); window.grab().save(str(output / 'desktop-gear-shortcuts.png'))
            checks['shortcutsUndo'] = bytes(window.backend.call('working')) == original and not window.pending()
            late_bag = bytearray(original); free_slots = [17, 22, 35, 48, 55, 59]
            for slot in range(60): struct.pack_into('<H', late_bag, 0x5bd8 + slot * 28, 501 | (1 << 11))
            for slot in free_slots: late_bag[0x5bd8 + slot * 28:0x5bd8 + (slot + 1) * 28] = bytes(28)
            struct.pack_into('<I', late_bag, 0, zlib.crc32(late_bag[4:-224]))
            for key in ('staff-balanced', 'staff-damage'):
                window.open_bytes(late_bag, 'synthetic-late-bag.sav')
                page('gear'); window.gear_consent.setChecked(True); window.gear_buttons[key].click()
                bag = window.backend.call('inventory', container='bag')
                checks[f'{key}AnyBagSlot'] = [bag[slot]['id'] for slot in free_slots] == [501, 595, 749, 706, 729, 665] and valid(window.backend.build())
                window.backend.call('undo'); window.refresh()
                checks[f'{key}AnyBagSlotUndo'] = bytes(window.backend.call('working')) == bytes(late_bag)
            if not all(checks.values()) or window.test_errors: raise AssertionError((checks, window.test_errors))
            (output / 'desktop-test.json').write_text(json.dumps({'passed': True, 'native': True, 'version': app.applicationVersion(), 'checks': checks}, indent=2), encoding='utf-8')
            window.closing = True; app.exit(0)
        except Exception as error:
            (output / 'desktop-test.json').write_text(json.dumps({'passed': False, 'error': str(error), 'checks': checks}, indent=2), encoding='utf-8')
            window.closing = True; app.exit(1)
        finally:
            window.ui_language_combo.setCurrentIndex(window.ui_language_combo.findData(saved_mode))

    QTimer.singleShot(0, exercise)
