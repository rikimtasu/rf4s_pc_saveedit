"""Test actual native Qt controls and an exported synthetic save, never a personal save."""
import json
from pathlib import Path
import struct
import zlib

from PySide6.QtCore import QTimer
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

    def exercise():
        checks = {}
        try:
            if game: window.load_references(all_references(game))
            original = bytes(window.backend.call('demoBytes'))
            window.open_bytes(original, 'synthetic.sav')
            select_page('inventory')
            form = window.inventory_form
            form.allow.setChecked(True)
            edit(form, 'craft0', 839)
            edit(form, 'element', 1)
            checks['itemDraftGuard'] = window.pending() and not window.export_action.isEnabled()
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
            select_page('player')
            form = window.player_form; form.allow.setChecked(True)
            edit(form, 'money', '1234'); form.apply_button.click()
            checks['sevenLanguages'] = window.language_combo.count() == 7
            window.language_combo.setCurrentIndex(window.language_combo.findData('zh-Hans'))
            checks['localizedNames'] = window.item_name(1) == '卷心菜'
            for key in ['calendar', 'skills', 'recipes', 'friendship', 'people', 'monsters', 'trophies', 'flags', 'raw', 'reference', 'review']:
                select_page(key)
            checks['allNativePages'] = not window.test_errors
            checks['noDrafts'] = not window.pending()
            exported = window.export_bytes()
            checks['checksum'] = len(exported) == 140424 and struct.unpack_from('<I', exported)[0] == zlib.crc32(exported[4:-224])
            checks['money'] = struct.unpack_from('<i', exported, 0x4c)[0] == 1234
            checks['originalUnchanged'] = bytes(window.backend.call('original')) == original
            if not all(checks.values()): raise AssertionError(checks)
            window.write_file(output / 'synthetic.edited.sav', exported)
            window.last_export = bytes(window.backend.call('working'))
            select_page('inventory')
            window.grab().save(str(output / 'desktop.png'))
            system = bytearray(9304); system[:4] = b'RF4D'
            struct.pack_into('<I', system, 4, zlib.crc32(system[8:]))
            window.open_bytes(system, 'rf4_sys.sav')
            select_page('system')
            window.system_form.allow.setChecked(True)
            edit(window.system_form, '2', 1)
            window.system_form.apply_button.click()
            system_output = window.export_bytes()
            checks['systemNativeControls'] = struct.unpack_from('<I', system_output, 8)[0] == 4 and struct.unpack_from('<I', system_output, 4)[0] == zlib.crc32(system_output[8:])
            if not all(checks.values()) or window.test_errors: raise AssertionError((checks, window.test_errors))
            (output / 'desktop-test.json').write_text(json.dumps({'passed': True, 'native': True, 'checks': checks}, indent=2), encoding='utf-8')
            window.closing = True
            app.exit(0)
        except Exception as error:
            (output / 'desktop-test.json').write_text(json.dumps({'passed': False, 'detail': str(error), 'checks': checks}, indent=2), encoding='utf-8')
            window.closing = True
            app.exit(1)

    QTimer.singleShot(0, exercise)
