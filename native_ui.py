"""Native Qt Widgets save editor. No web views, HTML rendering or server."""
import json
from pathlib import Path

from PySide6.QtCore import Qt, QSignalBlocker, Signal, QSaveFile, QIODevice
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGridLayout, QLabel, QPushButton, QCheckBox, QLineEdit, QComboBox, QGroupBox,
    QScrollArea, QStackedWidget, QListWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFileDialog, QMessageBox, QPlainTextEdit, QSplitter)

from native_save import NativeSave, local_references
from scripts.game_sources import all_references, LANGUAGES, parse_text


def combo_options(combo, choices, selected=None):
    with QSignalBlocker(combo):
        combo.clear()
        for label, value in choices:
            combo.addItem(str(label), value)
        index = combo.findData(selected)
        if index < 0 and selected is not None:
            combo.addItem(f'Unrecognized stored value {selected} · keep unless verified', selected)
            index = combo.count() - 1
        combo.setCurrentIndex(max(0, index))


class EditForm(QWidget):
    draftChanged = Signal()
    applyRequested = Signal()
    cleared = Signal()

    def __init__(self, fields, note='', parent=None):
        super().__init__(parent)
        self.fields = {field['key']: field for field in fields}
        self.controls = {}
        self.base = {}
        self.drafts = {}
        self.syncing = False
        layout = QVBoxLayout(self)
        self.allow = QCheckBox('Enable editing')
        layout.addWidget(self.allow)
        self.body = QWidget()
        grid = QGridLayout(self.body)
        for index, field in enumerate(fields):
            key = field['key']
            label = QLabel(field.get('label', key))
            kind = field.get('kind', 'number')
            if kind == 'bool':
                control = QCheckBox()
                control.toggled.connect(lambda _value, key=key: self.track(key))
            elif kind == 'choice':
                control = QComboBox()
                if field.get('search'):
                    control.setEditable(True)
                    control.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
                    control.completer().setFilterMode(Qt.MatchFlag.MatchContains)
                    control.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                    control.lineEdit().textEdited.connect(lambda _value, key=key: self.track(key))
                control.currentIndexChanged.connect(lambda _value, key=key: self.track(key))
                combo_options(control, field.get('choices', []))
            else:
                control = QLineEdit()
                control.textEdited.connect(lambda _value, key=key: self.track(key))
                if field.get('optional'):
                    control.setPlaceholderText('Blank keeps existing values')
                elif 'min' in field:
                    control.setToolTip(f'{field["min"]}–{field["max"]}; whole numbers only')
            self.controls[key] = control
            rows = (len(fields) + 1) // 2
            column = (index // rows) * 2 if len(fields) > 12 else 0
            row = index % rows if len(fields) > 12 else index
            grid.addWidget(label, row, column)
            grid.addWidget(control, row, column + 1)
        layout.addWidget(self.body)
        hint = QLabel(note)
        hint.setWordWrap(True)
        layout.addWidget(hint)
        footer = QHBoxLayout()
        self.status = QLabel('No draft')
        footer.addWidget(self.status, 1)
        clear = QPushButton('Clear draft')
        clear.clicked.connect(self.clear)
        self.apply_button = QPushButton('Apply changes')
        self.apply_button.clicked.connect(self.applyRequested)
        footer.addWidget(clear)
        footer.addWidget(self.apply_button)
        layout.addLayout(footer)
        self.allow.toggled.connect(self.enabled_changed)
        self.set_ready(False)

    def enabled_changed(self):
        self.body.setEnabled(self.allow.isEnabled() and self.allow.isChecked())
        self.apply_button.setEnabled(self.allow.isEnabled() and self.allow.isChecked())
        self.draftChanged.emit()

    def set_ready(self, ready):
        self.allow.setEnabled(ready)
        self.enabled_changed()

    def value(self, key):
        control = self.controls[key]
        if isinstance(control, QCheckBox):
            return int(control.isChecked())
        if isinstance(control, QComboBox):
            if control.isEditable() and control.currentText() != control.itemText(control.currentIndex()):
                raise ValueError('Choose a matching item from the list; typed names are not item IDs.')
            return control.currentData()
        return control.text()

    def track(self, key):
        if self.syncing:
            return
        try:
            value = self.value(key)
            base = self.base.get(key)
            same = value == base or (value not in ('', None) and str(value) == str(base))
            if self.fields[key].get('optional') and value == '' and base is None:
                same = True
        except ValueError:
            value, same = '', False
        if same:
            self.drafts.pop(key, None)
        else:
            self.drafts[key] = value
        self.status.setText('Draft pending · apply or clear before export' if self.drafts else 'No draft')
        self.draftChanged.emit()

    def write(self, key, value):
        control = self.controls[key]
        with QSignalBlocker(control):
            if isinstance(control, QCheckBox):
                control.setChecked(bool(value))
            elif isinstance(control, QComboBox):
                index = control.findData(value)
                if index < 0:
                    control.addItem(f'Unrecognized stored ID {value}', value)
                    index = control.count() - 1
                control.setCurrentIndex(index)
            else:
                control.setText('' if value is None else str(value))

    def set_data(self, values, choices=None):
        self.syncing = True
        try:
            for key, control in self.controls.items():
                current = self.drafts.get(key, values.get(key))
                if choices and key in choices:
                    combo_options(control, choices[key], current)
                self.base[key] = values.get(key)
                self.write(key, current)
        finally:
            self.syncing = False

    def changes(self):
        if not self.allow.isChecked() or not self.allow.isEnabled():
            raise ValueError('Enable this editor first.')
        return {key: self.value(key) for key in self.drafts}

    def clear(self):
        self.drafts.clear()
        self.set_data(self.base)
        self.status.setText('No draft')
        self.draftChanged.emit()
        self.cleared.emit()


class NativeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.backend = NativeSave()
        self.constants = self.backend.constants
        self.languages = {}
        self.language = 'en'
        self.item_names = {}
        self.source_path = None
        self.last_export = None
        self.closing = False
        self.demo_mode = False
        self.forms = []
        self.renderers = {}
        self.pages = {}
        self.inventory_container = 'bag'
        self.inventory_slot = 0
        self.candidate = 1
        self.selections = {'skills': 0, 'friendship': 1, 'people': 1, 'monsters': None, 'recipes': None, 'trophies': None, 'flags': None}
        self.setWindowTitle('Rune Factory 4 Special · Native save editor')
        self.resize(1160, 850)
        self.setMinimumSize(850, 600)
        toolbar = self.addToolBar('Save and references')
        toolbar.setMovable(False)
        for title, callback, shortcut in [('Open save', self.open_file, QKeySequence.StandardKey.Open), ('Undo', lambda: self.mutate('undo'), QKeySequence.StandardKey.Undo), ('Redo', lambda: self.mutate('redo'), QKeySequence.StandardKey.Redo), ('Read game folder', self.read_game, None)]:
            action = QAction(title, self)
            action.triggered.connect(callback)
            if shortcut:
                action.setShortcut(QKeySequence(shortcut))
            toolbar.addAction(action)
            if title == 'Undo': self.undo_action = action
            if title == 'Redo': self.redo_action = action
        toolbar.addSeparator()
        toolbar.addWidget(QLabel('Game names: '))
        self.language_combo = QComboBox()
        self.language_combo.currentIndexChanged.connect(self.select_language)
        toolbar.addWidget(self.language_combo)
        self.export_action = QAction('Export edited save', self)
        self.export_action.setShortcut(QKeySequence.StandardKey.Save)
        self.export_action.triggered.connect(self.export_file)
        toolbar.addAction(self.export_action)
        splitter = QSplitter()
        self.navigation = QListWidget()
        self.navigation.setMaximumWidth(210)
        self.stack = QStackedWidget()
        splitter.addWidget(self.navigation)
        splitter.addWidget(self.stack)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)
        self.make_overview()
        self.make_calendar()
        self.make_player()
        self.make_inventory()
        self.make_record_pages()
        self.make_marriage()
        self.make_system()
        self.make_flags()
        self.make_reference()
        self.make_raw()
        self.make_review()
        self.navigation.currentRowChanged.connect(self.select_page)
        references = local_references()
        self.load_references(references)
        self.navigation.setCurrentRow(0)
        self.refresh()

    def page(self, key, title, note=''):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        heading = QLabel(title)
        font = heading.font(); font.setPointSize(17); font.setBold(True); heading.setFont(font)
        layout.addWidget(heading)
        if note:
            hint = QLabel(note); hint.setWordWrap(True); layout.addWidget(hint)
        self.pages[key] = (widget, layout, self.navigation.count())
        self.navigation.addItem(title)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(widget)
        self.stack.addWidget(scroll)
        return layout

    def form(self, layout, fields, callback, note=''):
        form = EditForm(fields, note)
        layout.addWidget(form)
        layout.addStretch()
        form.draftChanged.connect(self.update_export)
        form.applyRequested.connect(lambda: self.attempt(lambda: self.apply_form(form, callback)))
        form.cleared.connect(self.refresh)
        self.forms.append(form)
        return form

    def apply_form(self, form, callback):
        changes = form.changes()
        if not changes:
            return
        callback(changes)
        form.drafts.clear()
        form.status.setText('No draft')
        self.refresh()
        self.statusBar().showMessage('Changes applied in memory. Review and export; the original is untouched.', 10000)

    def attempt(self, action):
        try:
            return action()
        except (ValueError, OSError, KeyError) as error:
            self.statusBar().showMessage(str(error))
            if not getattr(self, 'testing', False):
                QMessageBox.warning(self, 'Edit not applied', str(error))
            else:
                self.test_errors.append(str(error))

    def pending(self):
        return any(form.drafts for form in self.forms)

    def update_export(self):
        state = self.backend.state()
        self.export_action.setEnabled(bool(state) and not self.pending() and not self.demo_mode)
        self.export_action.setToolTip('Apply or clear drafts before export.' if self.pending() else 'Download an edited copy; keep a backup.')

    def select_page(self, index):
        if index < 0:
            return
        self.stack.setCurrentIndex(index)
        self.refresh_page()

    def refresh_page(self):
        for key, (_widget, _layout, index) in self.pages.items():
            if index == self.stack.currentIndex() and key in self.renderers:
                self.attempt(self.renderers[key])

    def refresh(self):
        state = self.backend.state()
        self.undo_action.setEnabled(bool(state and state['undo']))
        self.redo_action.setEnabled(bool(state and state['redo']))
        slot = bool(state and state['kind'] == 'slot')
        always = {'overview', 'reference', 'review'}
        for key, (_widget, _layout, index) in self.pages.items():
            available = key in always or bool(state) and (key in {'raw'} or slot and key != 'system' or not slot and key == 'system')
            if key in {'player', 'inventory'}:
                available = slot and state['playerProfile']
            item = self.navigation.item(index)
            item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled if available else Qt.ItemFlag.NoItemFlags)
        self.overview_status.setText('No save loaded' if not state else f'{state["name"]}\n{state["platform"].upper()} · {state["size"]:,} bytes · CRC {"valid" if state["crcValid"] else "mismatch (repair consent required)"}\n{state["changedBytes"]:,} changed bytes · {state["undo"]} undoable edits')
        self.refresh_page()
        self.update_export()

    def mutate(self, operation, **args):
        self.attempt(lambda: self.backend.call(operation, **args))
        self.refresh()

    def open_bytes(self, data, name, path=None, demo=False):
        self.backend.open(data, name)
        self.source_path = path
        self.last_export = None
        self.demo_mode = demo
        self.export_platform.setCurrentIndex(self.export_platform.findData('keep'))
        self.export_gender.setCurrentIndex(self.export_gender.findData('keep'))
        self.conversion_consent.setChecked(False)
        self.repair_consent.setChecked(False)
        self.reset_appearance.setChecked(False)
        for form in self.forms:
            form.drafts.clear(); form.base.clear(); form.allow.setChecked(False)
        self.inventory_container = 'bag'; self.inventory_slot = 0
        self.candidate = 1
        self.refresh()

    def discard_confirmation(self):
        state = self.backend.state()
        if not self.pending() and not (state and state['dirty'] and self.last_export != bytes(self.backend.call('working'))):
            return True
        return QMessageBox.question(self, 'Unexported changes', 'Discard unexported edits and drafts?', QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel) == QMessageBox.StandardButton.Discard

    def open_file(self):
        if not self.discard_confirmation(): return
        filename, _ = QFileDialog.getOpenFileName(self, 'Open a slot or system save', '', 'RF4S saves (*.sav)')
        if filename:
            self.attempt(lambda: self.open_bytes(Path(filename).read_bytes(), Path(filename).name, Path(filename)))

    def make_overview(self):
        layout = self.page('overview', 'Save overview', 'Native desktop controls · offline · no browser or local server. Back up your save folder and close the game before editing.')
        self.overview_status = QLabel(); self.overview_status.setWordWrap(True); layout.addWidget(self.overview_status)
        for title, callback in [('Open save', self.open_file), ('Try synthetic demo', lambda: self.attempt(self.demo)), ('Read game folder', self.read_game), ('Read extracted item tables', lambda: self.read_tables('importItems')), ('Read extracted recipe tables', lambda: self.read_tables('importRecipes')), ('Read extracted language names', self.read_languages)]:
            button = QPushButton(title); button.clicked.connect(callback); layout.addWidget(button)
        layout.addStretch()

    def demo(self):
        if self.discard_confirmation():
            self.open_bytes(bytes(self.backend.call('demoBytes')), 'Synthetic demo.sav (not playable; export disabled)', demo=True)

    def load_references(self, data):
        if self.pending(): raise ValueError('Apply or clear drafts before replacing game references.')
        self.backend.call('references', items=data.get('items'), recipes=data.get('recipes'))
        self.languages = (data.get('languages') or {}).get('languages', {})
        self.item_names = {item['id']: item['name'] for item in self.backend.call('items')}
        self.update_languages()

    def read_game(self):
        if self.pending():
            self.attempt(lambda: (_ for _ in ()).throw(ValueError('Apply or clear drafts before reading game references.')))
            return
        folder = QFileDialog.getExistingDirectory(self, 'Choose game folder containing Bundle')
        if folder:
            self.attempt(lambda: self.load_references(all_references(folder)))
            self.refresh()

    def read_tables(self, operation):
        if self.pending():
            self.attempt(lambda: (_ for _ in ()).throw(ValueError('Apply or clear drafts before replacing references.')))
            return
        paths, _ = QFileDialog.getOpenFileNames(self, 'Read extracted definition tables', '', 'Game tables (*.bin)')
        if paths:
            def load():
                if len(paths) > (4 if operation == 'importItems' else 21): raise ValueError('Too many reference tables.')
                files = []
                for filename in paths:
                    path = Path(filename)
                    if path.stat().st_size > 16 * 1024 * 1024: raise ValueError('Reference table is too large.')
                    files.append({'name': path.name, 'bytes': list(path.read_bytes())})
                self.backend.call(operation, files=files)
                self.item_names = {item['id']: item['name'] for item in self.backend.call('items')}
            self.attempt(load); self.refresh()

    def read_languages(self):
        paths, _ = QFileDialog.getOpenFileNames(self, 'Read extracted name tables', '', 'Game names (*.eng *.jpn *.fra *.deu *.kor *.twn *.chn)')
        def load():
            staged = {key: dict(value) for key, value in self.languages.items()}
            if len(paths) > 21: raise ValueError('Read up to 21 name tables.')
            for filename in paths:
                path = Path(filename)
                parts = path.name.split('.')
                if len(parts) != 2 or parts[1] not in LANGUAGES: raise ValueError('Choose supported game TEXT name tables.')
                kind = {'rf3TxtItem_split2_1': 'items', 'rf3TxtNpc_split2_1': 'people', 'rf3TxtSkill_split2_1': 'skills'}.get(parts[0])
                if not kind or path.stat().st_size > 16 * 1024 * 1024: raise ValueError('Choose name tables, not descriptions.')
                code, label = LANGUAGES[parts[1]]
                staged.setdefault(code, {'label': label})[kind] = parse_text(path.read_bytes())
            self.languages = staged; self.update_languages(); self.refresh()
        if paths: self.attempt(load)

    def update_languages(self):
        choices = [('English', 'en')] + [(entry['label'], code) for code, entry in self.languages.items() if code != 'en']
        if self.language not in {code for _label, code in choices}: self.language = 'en'
        combo_options(self.language_combo, choices, self.language)

    def select_language(self):
        self.language = self.language_combo.currentData() or 'en'
        self.refresh_page()

    def name(self, kind, index, fallback):
        names = self.languages.get(self.language, {}).get(kind, [])
        return names[index] if 0 <= index < len(names) and names[index] else fallback

    def item_name(self, index):
        return self.name('items', index, self.item_names.get(index, f'Unknown item {index}'))

    def person_name(self, index):
        fallback = self.constants['people'][index]
        return fallback if index in (22, 23) else self.name('people', index, fallback)

    def make_calendar(self):
        layout = self.page('calendar', 'Calendar', 'Direct date changes do not simulate daily game updates.')
        fields = [{'key': 'day', 'label': 'Day', 'min': 1, 'max': 30}, {'key': 'season', 'label': 'Season', 'kind': 'choice', 'choices': [(name, i) for i, name in enumerate(self.constants['seasons'])]}, {'key': 'year', 'label': 'Year', 'min': 1, 'max': 0xffffffff}]
        self.calendar_form = self.form(layout, fields, lambda changes: self.backend.call('setCalendar', changes={**self.calendar_form.base, **changes}))
        def render():
            state = self.backend.state(); self.calendar_form.set_ready(bool(state and state['kind'] == 'slot'))
            if state and state['calendar']: self.calendar_form.set_data(state['calendar'])
        self.renderers['calendar'] = render

    def make_player(self):
        layout = self.page('player', 'Player values', 'Base values only; equipment-adjusted attributes are not recalculated.')
        fields = [{'key': key, **spec} for key, spec in self.constants['player'].items()]
        self.player_form = self.form(layout, fields, lambda changes: self.backend.call('setPlayer', changes=changes))
        def render():
            state = self.backend.state(); ready = bool(state and state['playerProfile']); self.player_form.set_ready(ready)
            if ready: self.player_form.set_data(self.backend.call('player'))
        self.renderers['player'] = render

    def make_inventory(self):
        layout = self.page('inventory', 'Bag & storage', 'Saved slots do not unlock capacity. Replacements clear previous metadata. Element changes append crystals without deleting existing upgrades; test equipment edits in-game.')
        top = QHBoxLayout()
        self.container_combo = QComboBox()
        combo_options(self.container_combo, [(spec['label'], key) for key, spec in self.constants['inventories'].items()], 'bag')
        self.container_combo.currentIndexChanged.connect(self.change_container)
        self.inventory_search = QLineEdit(); self.inventory_search.setPlaceholderText('Filter saved items by name or slot')
        self.inventory_search.textChanged.connect(self.render_inventory_table)
        self.all_slots = QCheckBox('Show empty slots'); self.all_slots.toggled.connect(self.render_inventory_table)
        top.addWidget(self.container_combo); top.addWidget(self.inventory_search, 1); top.addWidget(self.all_slots)
        layout.addLayout(top)
        self.inventory_table = QTableWidget(0, 4)
        self.inventory_table.setHorizontalHeaderLabels(['Saved slot', 'Item', 'Quantity', 'Levels'])
        self.inventory_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.inventory_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.inventory_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.inventory_table.setMaximumHeight(240)
        self.inventory_table.itemSelectionChanged.connect(self.change_inventory_slot)
        layout.addWidget(self.inventory_table)
        self.slot_label = QLabel(); layout.addWidget(self.slot_label)
        fields = [{'key': 'id', 'label': 'Item (type to search)', 'kind': 'choice', 'search': True}, {'key': 'quantity', 'label': 'Quantity'}, {'key': 'level', 'label': 'Set all item levels', 'optional': True}, {'key': 'element', 'label': 'Weapon / tool element', 'kind': 'choice', 'choices': [('Keep existing', None)] + [(item['name'], item['value']) for item in self.constants['elements']]}, {'key': 'inherited', 'label': 'Inherited equipment', 'kind': 'choice', 'search': True}, {'key': 'totalLevel', 'label': 'Total-level bonus (0–150)'}, {'key': 'rarityBonus', 'label': 'Rarity bonus (0–200)'}, *[{'key': f'craft{i}', 'label': f'Crafting attachment {i + 1}', 'kind': 'choice', 'search': True} for i in range(3)], *[{'key': f'upgrade{i}', 'label': f'Upgrade {i + 1} · level {i + 2}', 'kind': 'choice', 'search': True} for i in range(9)]]
        self.inventory_form = self.form(layout, fields, self.apply_inventory, 'Attachment IDs are 10-bit (0–1023), equipment only. Unchanged fields are preserved; 0 removes an attachment. Blank level preserves mixed unit levels.')
        self.inventory_form.controls['id'].currentIndexChanged.connect(self.inventory_id_changed)
        self.renderers['inventory'] = self.render_inventory

    def change_container(self):
        selected = self.container_combo.currentData()
        if self.inventory_form.drafts:
            with QSignalBlocker(self.container_combo): self.container_combo.setCurrentIndex(self.container_combo.findData(self.inventory_container))
            self.statusBar().showMessage('Apply or clear item drafts before switching containers.'); return
        self.inventory_container = selected; self.inventory_slot = 0; self.render_inventory()

    def change_inventory_slot(self):
        selected = self.inventory_table.selectedItems()
        if not selected: return
        slot = selected[0].data(Qt.ItemDataRole.UserRole)
        if slot == self.inventory_slot: return
        if self.inventory_form.drafts:
            self.statusBar().showMessage('Apply or clear item drafts before switching slots.'); self.render_inventory_table(); return
        self.inventory_slot = slot; self.render_inventory()

    def inventory_id_changed(self):
        form = self.inventory_form
        if form.syncing or not form.allow.isChecked(): return
        item_id = form.controls['id'].currentData()
        if item_id == form.base.get('id'): return
        def update():
            limit = self.backend.call('definition', id=item_id)['stack']
            form.write('quantity', 0 if not item_id else min(limit, max(1, int(form.value('quantity') or 1))))
            form.track('quantity')
        self.attempt(update)

    def render_inventory_table(self):
        state = self.backend.state()
        if not state or not state['playerProfile']: return
        items = self.backend.call('inventory', container=self.inventory_container)
        query = self.inventory_search.text().casefold().strip()
        items = [item for item in items if (item['id'] or self.all_slots.isChecked()) and (not query or query in f'{item["slot"] + 1} {self.item_name(item["id"])}'.casefold())]
        with QSignalBlocker(self.inventory_table):
            self.inventory_table.setRowCount(len(items))
            for row, item in enumerate(items):
                values = [item['slot'] + 1, self.item_name(item['id']) if item['id'] else 'Empty', item['quantity'], ', '.join(map(str, item['levels']))]
                for column, value in enumerate(values):
                    cell = QTableWidgetItem(str(value)); cell.setData(Qt.ItemDataRole.UserRole, item['slot']); self.inventory_table.setItem(row, column, cell)
                if item['slot'] == self.inventory_slot: self.inventory_table.selectRow(row)

    def render_inventory(self):
        state = self.backend.state(); ready = bool(state and state['playerProfile']); self.inventory_form.set_ready(ready)
        if not ready: return
        with QSignalBlocker(self.container_combo): self.container_combo.setCurrentIndex(self.container_combo.findData(self.inventory_container))
        self.render_inventory_table()
        item = self.backend.call('item', container=self.inventory_container, slot=self.inventory_slot)
        available = self.backend.call('items', editableOnly=True)
        choices = [(self.item_name(entry['id']), entry['id']) for entry in available]
        choices.sort(key=lambda choice: choice[0].casefold())
        attachments = [('None / remove · 0', 0)] + [(f'{label} · {value}', value) for label, value in choices if value <= 1023]
        inherited = [('None · 0', 0)] + [(f'{self.item_name(entry["id"])} · {entry["id"]}', entry['id']) for entry in available if entry['id'] <= 1023 and entry['category'] in (15,16,17,18,19,24,25,26,27,28,29,30,31,32,33,34,35,36,37)]
        options = {key: attachments for key in self.inventory_form.controls if key.startswith(('craft', 'upgrade'))}
        options.update(id=[('Empty / clear slot · 0', 0)] + [(f'{label} · {value}', value) for label, value in choices], inherited=inherited)
        self.inventory_form.set_data({'id': item['id'], 'quantity': item['quantity'], 'level': None, 'element': None, **item['details']}, options)
        self.slot_label.setText(f'Saved slot {self.inventory_slot + 1} · {self.item_name(item["id"])} · current element: {next((entry["name"] for entry in self.constants["elements"] if entry["value"] == item["element"]), "not recognized / not a weapon")}.')

    def apply_inventory(self, changes):
        basic = {'id': self.inventory_form.value('id'), 'quantity': self.inventory_form.value('quantity')}
        if changes.get('level') not in (None, ''): basic['level'] = changes['level']
        details = {key: value for key, value in changes.items() if key not in {'id', 'quantity', 'level'} and value is not None}
        self.backend.call('setItem', container=self.inventory_container, slot=self.inventory_slot, changes=basic, details=details)

    def make_record_pages(self):
        self.record_forms = {}
        self.record_selectors = {}
        specs = {
            'skills': ('Skills', [{'key': 'level', 'label': 'Skill level'}, {'key': 'xp', 'label': 'Experience (0–16,777,215)'}], 'Direct skill levels do not award stat gains. Crafting / resistance skills cap at 99; others at 999.'),
            'recipes': ('Learned recipes', [{'key': 'known', 'label': 'Recipe learned', 'kind': 'bool'}], 'Variants sharing a learned bit change together. Recipe difficulty is not stored as an editable save value.'),
            'friendship': ('Friendship', [{'key': 'level', 'label': 'Friendship level (0–10,000)'}], 'Does not trigger dating, wedding or story events.'),
            'people': ('People stats', [{'key': key, **field} for key, field in self.constants['stats'].items()], 'Stored base stats only; no spawning or derived-stat recalculation.'),
            'monsters': ('Tamed monsters', [{'key': 'friendship', 'label': 'Friendship (0–1,000)'}, *[{'key': key, **field} for key, field in self.constants['stats'].items()]], 'Existing tamed monsters only. Names, species and barns are preserved.'),
            'trophies': ('Trophy records', [{'key': 'value', 'label': 'Recorded result', 'kind': 'choice'}], 'Recorded game results only, not physical trophies or Steam achievements.'),
        }
        for key, (title, fields, note) in specs.items():
            layout = self.page(key, title, note)
            selector = QComboBox()
            layout.addWidget(selector)
            self.record_selectors[key] = selector
            if key == 'recipes':
                row = QHBoxLayout()
                self.recipe_group = QComboBox()
                combo_options(self.recipe_group, [('All groups', 'all')] + [(label, kind) for kind, label in self.constants['recipeGroups'].items()], 'all')
                self.recipe_search = QLineEdit(); self.recipe_search.setPlaceholderText('Filter recipe result names')
                self.recipe_group.currentIndexChanged.connect(self.filter_recipes)
                self.recipe_search.textChanged.connect(self.filter_recipes)
                row.addWidget(self.recipe_group); row.addWidget(self.recipe_search, 1); layout.addLayout(row)
                row = QHBoxLayout()
                for title, known in [('Learn filtered recipes', True), ('Forget filtered recipes', False)]:
                    button = QPushButton(title); button.clicked.connect(lambda _checked=False, known=known: self.attempt(lambda: self.bulk_recipes(known))); row.addWidget(button)
                layout.addLayout(row)
            form = self.form(layout, fields, lambda changes, key=key: self.apply_record(key, changes))
            self.record_forms[key] = form
            selector.currentIndexChanged.connect(lambda _index, key=key: self.change_record(key))
            self.renderers[key] = lambda key=key: self.render_record(key)

    def filtered_recipes(self):
        records = self.backend.call('recipes')
        group = self.recipe_group.currentData()
        query = self.recipe_search.text().strip().casefold()
        return [record for record in records if (group == 'all' or record['kind'] == group) and (not query or query in f'{self.item_name(record["result"])} {record["result"]}'.casefold())]

    def filter_recipes(self):
        if 'recipes' not in self.record_forms: return
        if self.record_forms['recipes'].drafts:
            self.statusBar().showMessage('Clear or apply the recipe draft before selecting another recipe.')
        self.render_record('recipes')

    def change_record(self, key):
        form = self.record_forms[key]
        selector = self.record_selectors[key]
        selected = selector.currentData()
        if selected == self.selections[key]: return
        if form.drafts:
            with QSignalBlocker(selector): selector.setCurrentIndex(selector.findData(self.selections[key]))
            self.statusBar().showMessage('Apply or clear this draft before selecting another record.'); return
        self.selections[key] = selected
        self.render_record(key)

    def render_record(self, key):
        form = self.record_forms[key]
        state = self.backend.state()
        ready = bool(state and state['kind'] == 'slot')
        form.set_ready(ready)
        if not ready: return
        if key == 'people':
            records = [{'id': i, 'name': self.person_name(i)} for i in range(1, 27)]
        elif key == 'recipes':
            records = self.filtered_recipes()
        else:
            records = self.backend.call(key)
        choices = []
        for record in records:
            if key == 'skills': label, value = self.name('skills', record['id'], record['name']), record['id']
            elif key == 'friendship': label, value = self.person_name(record['id']), record['id']
            elif key == 'people': label, value = record['name'], record['id']
            elif key == 'monsters': label, value = f'{record["id"] + 1} · {record["name"] or "Unnamed"} · species {record["species"]}', record['id']
            elif key == 'recipes': label, value = f'{self.item_name(record["result"])} · difficulty {record["level"]} · variant {record["index"]}', f'{record["kind"]}:{record["index"]}'
            else: label, value = record['label'], record['name']
            choices.append((label, value))
        selected = self.selections[key]
        if selected not in {value for _label, value in choices} and not form.drafts:
            selected = choices[0][1] if choices else None
            self.selections[key] = selected
        combo_options(self.record_selectors[key], choices, selected)
        form.set_ready(bool(choices))
        if not choices: return
        record = next((record for record in records if (f'{record["kind"]}:{record["index"]}' if key == 'recipes' else record['name'] if key == 'trophies' else record['id']) == selected), None)
        if record is None: return
        options = None
        if key == 'people': values = self.backend.call('stats', kind='person', id=selected)
        elif key == 'monsters': values = {**self.backend.call('stats', kind='monster', id=selected), 'friendship': record['friendship']}
        elif key == 'trophies':
            values = {'value': record['value']}
            labels = ['Not recorded', 'Recorded'] if record['width'] == 1 else ['None', 'Gold / first', 'Silver / second', 'Bronze / third']
            options = {'value': [(label, index) for index, label in enumerate(labels)]}
        else: values = record
        form.set_data(values, options)

    def apply_record(self, key, changes):
        selected = self.selections[key]
        if key == 'skills': self.backend.call('setSkill', id=selected, changes=changes)
        elif key == 'friendship': self.backend.call('setFriendship', id=selected, level=changes['level'])
        elif key == 'people': self.backend.call('setStats', kind='person', id=selected, changes=changes)
        elif key == 'monsters':
            values = {'stats': {field: value for field, value in changes.items() if field != 'friendship'}}
            if 'friendship' in changes: values['friendship'] = changes['friendship']
            self.backend.call('setMonster', id=selected, changes=values)
        elif key == 'trophies': self.backend.call('setTrophy', name=selected, value=changes['value'])
        else:
            record = next(record for record in self.backend.call('recipes') if f'{record["kind"]}:{record["index"]}' == selected)
            self.backend.call('setRecipes', recipes=[record], known=bool(changes['known']))

    def bulk_recipes(self, known):
        if not self.record_forms['recipes'].allow.isChecked() or self.record_forms['recipes'].drafts:
            raise ValueError('Enable recipe editing and apply / clear its draft first.')
        records = list({record['bitOffset']: record for record in self.filtered_recipes()}.values())
        self.backend.call('setRecipes', recipes=records, known=known)
        self.refresh()

    def make_marriage(self):
        layout = self.page('marriage', 'Marriage flags', 'Flags only—not a complete marry/divorce operation. Wedding events, pregnancy, children, schedules and system unlocks are not simulated. Back up and test the exported copy.')
        self.marriage_summary = QLabel(); layout.addWidget(self.marriage_summary)
        self.candidate_combo = QComboBox()
        layout.addWidget(QLabel('Event candidate (does not change spouse)')); layout.addWidget(self.candidate_combo)
        self.candidate_combo.currentIndexChanged.connect(self.change_candidate)
        fields = [{**field, 'kind': 'choice' if field['key'] in {'spouse', 'season'} else 'bool' if field['max'] == 1 else 'number'} for field in self.constants['marriage']]
        fields += [{'key': 'marriageEvent', 'label': 'Candidate marriage event cleared', 'kind': 'bool'}, {'key': 'newlywedEvent', 'label': 'Candidate newlywed event cleared', 'kind': 'bool'}]
        self.marriage_form = self.form(layout, fields, lambda changes: self.backend.call('setMarriage', candidate=self.candidate, changes=changes))
        self.renderers['marriage'] = self.render_marriage

    def change_candidate(self):
        if self.marriage_form.drafts:
            with QSignalBlocker(self.candidate_combo): self.candidate_combo.setCurrentIndex(self.candidate_combo.findData(self.candidate))
            self.statusBar().showMessage('Apply or clear marriage drafts before switching candidates.'); return
        self.candidate = self.candidate_combo.currentData()
        self.render_marriage()

    def render_marriage(self):
        state = self.backend.state(); ready = bool(state and state['kind'] == 'slot'); self.marriage_form.set_ready(ready)
        candidates = [(self.person_name(person['id']), person['id']) for person in self.constants['candidates']]
        combo_options(self.candidate_combo, candidates, self.candidate)
        if not ready: return
        values = self.backend.call('marriage', candidate=self.candidate)
        self.marriage_form.set_data(values, {'spouse': [('None · 0', 0)] + candidates, 'season': [(season, i) for i, season in enumerate(self.constants['seasons'])]})
        self.marriage_summary.setText(f'Spouse ID {values["spouse"]} · anniversary {self.constants["seasons"][values["season"]]} {values["day"] or "(unset)"}')

    def make_system(self):
        layout = self.page('system', 'System save unlocks', 'Persistent ending/wedding/data-transfer records only. These do not simulate events or advance slot saves.')
        self.system_form = self.form(layout, [{'key': str(field['bit']), 'label': field['label'], 'kind': 'bool'} for field in self.constants['systemFlags']], lambda changes: self.backend.call('setSystem', changes=changes))
        def render():
            state = self.backend.state(); ready = bool(state and state['kind'] == 'system'); self.system_form.set_ready(ready)
            if ready: self.system_form.set_data({str(field['bit']): field['value'] for field in self.backend.call('system')})
        self.renderers['system'] = render

    def make_flags(self):
        layout = self.page('flags', 'Expert: story flags', 'Story changes can break progression. These controls do not initialize world state, reward quests or replay events.')
        self.flag_search = QLineEdit(); self.flag_search.setPlaceholderText('Find flags / registers by developer name or description'); layout.addWidget(self.flag_search)
        self.flag_selector = QComboBox(); layout.addWidget(self.flag_selector)
        self.flag_search.textChanged.connect(self.render_flags)
        self.flag_selector.currentIndexChanged.connect(lambda: self.change_flag())
        self.flag_info = QLabel(); self.flag_info.setWordWrap(True); layout.addWidget(self.flag_info)
        self.flag_form = self.form(layout, [{'key': 'value', 'label': 'Value (1-bit flags: 0 or 1)'}], lambda changes: self.backend.call('setFlag', name=self.selections['flags'], value=changes['value']))
        row = QHBoxLayout()
        for label, callback in [('Read symbols', self.read_symbols), ('Download progress profile', self.save_profile), ('Read and apply profile', self.read_profile)]:
            button = QPushButton(label); button.clicked.connect(callback); row.addWidget(button)
        layout.addLayout(row)
        self.renderers['flags'] = self.render_flags

    def change_flag(self):
        selected = self.flag_selector.currentData()
        if self.flag_form.drafts:
            with QSignalBlocker(self.flag_selector): self.flag_selector.setCurrentIndex(self.flag_selector.findData(self.selections['flags']))
            self.statusBar().showMessage('Apply or clear the flag draft first.'); return
        self.selections['flags'] = selected
        self.render_flags()

    def render_flags(self):
        state = self.backend.state(); ready = bool(state and state['kind'] == 'slot'); self.flag_form.set_ready(ready)
        if not ready: return
        records = self.backend.call('flags')
        query = self.flag_search.text().strip().casefold()
        matching = [record for record in records if not query or query in f'{record["name"]} {record.get("label", "")} {record.get("description", "")}'.casefold()]
        selected = self.selections['flags']
        if not self.flag_form.drafts and selected not in {record['name'] for record in matching}:
            selected = matching[0]['name'] if matching else None; self.selections['flags'] = selected
        combo_options(self.flag_selector, [(record['name'], record['name']) for record in matching], selected)
        record = next((record for record in records if record['name'] == selected), None)
        self.flag_form.set_ready(bool(record))
        if record:
            self.flag_info.setText(f'Bit {record["bitOffset"]} · {record["width"]} bits · range 0–{2 ** record["width"] - 1}\n{record.get("label") or record.get("description", "")}')
            self.flag_form.set_data({'value': record['value']})

    def read_symbols(self):
        if self.pending(): self.statusBar().showMessage('Apply or clear drafts before replacing symbols.'); return
        filename, _ = QFileDialog.getOpenFileName(self, 'Read emdeb.bin', '', 'Developer symbols (*.bin)')
        if filename:
            def load():
                path = Path(filename)
                if path.stat().st_size > 5 * 1024 * 1024: raise ValueError('Symbol table is too large.')
                self.backend.call('importSymbols', bytes=list(path.read_bytes()))
            self.attempt(load); self.refresh()

    def save_profile(self):
        self.attempt(lambda: self.write_dialog(json.dumps(self.backend.call('profile'), indent=2).encode(), 'save.progress.json', 'Progress profile (*.json)'))

    def read_profile(self):
        if self.pending() or not self.flag_form.allow.isChecked():
            self.statusBar().showMessage('Enable flag editing and apply / clear drafts first.'); return
        filename, _ = QFileDialog.getOpenFileName(self, 'Read progress profile', '', 'Progress profile (*.json)')
        if not filename: return
        def load():
            path = Path(filename)
            if path.stat().st_size > 1024 * 1024: raise ValueError('Progress profile is too large.')
            text = path.read_text(encoding='utf-8')
            data = json.loads(text)
            count = len(data.get('flags', {}))
            if QMessageBox.question(self, 'Apply progression flags?', f'Apply {count} named flags as one undoable edit? Events and world state will not be simulated.', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel) == QMessageBox.StandardButton.Yes:
                self.backend.call('applyProfile', text=text)
        self.attempt(load); self.refresh()

    def make_reference(self):
        layout = self.page('reference', 'Read-only item reference', 'Game definitions are not saved instance stats. This does not edit game files.')
        self.reference_id = QLineEdit('1'); layout.addWidget(QLabel('Item ID')); layout.addWidget(self.reference_id)
        lookup = QPushButton('Look up definitions'); lookup.clicked.connect(lambda: self.attempt(self.render_reference)); layout.addWidget(lookup)
        self.reference_text = QPlainTextEdit(); self.reference_text.setReadOnly(True); layout.addWidget(self.reference_text)
        self.renderers['reference'] = self.render_reference

    def render_reference(self):
        item_id = int(self.reference_id.text(), 0)
        data = self.backend.call('reference', id=item_id)
        self.reference_text.setPlainText(self.item_name(item_id) + '\n' + json.dumps(data, ensure_ascii=False, indent=2))

    def make_raw(self):
        layout = self.page('raw', 'Expert: raw save fields', 'Use only independently verified offsets. The checksum header is protected; raw edits may break the save.')
        fields = [{'key': 'offset', 'label': 'File offset (decimal or 0x hex)'}, {'key': 'type', 'label': 'Integer type', 'kind': 'choice', 'choices': [(name, name) for name in ['u8','i8','u16','i16','u32','i32']]}, {'key': 'value', 'label': 'New integer value', 'optional': True}, {'key': 'bytes', 'label': 'OR hex bytes to patch', 'optional': True}]
        self.raw_form = self.form(layout, fields, self.apply_raw, 'Enter either a number or space-separated two-digit hex bytes, not both. At most 256 raw bytes per edit.')
        self.raw_current = QLabel(); layout.addWidget(self.raw_current)
        inspect = QPushButton('Inspect current integer'); inspect.clicked.connect(lambda: self.attempt(self.inspect_raw)); layout.addWidget(inspect)
        def render():
            state = self.backend.state(); self.raw_form.set_ready(bool(state))
            self.raw_form.set_data({'offset': '0x8' if state and state['kind'] == 'system' else '0x14', 'type': 'u32', 'value': None, 'bytes': None})
        self.renderers['raw'] = render

    def inspect_raw(self):
        self.raw_current.setText(str(self.backend.call('readNumber', offset=self.raw_form.value('offset'), type=self.raw_form.value('type'))))

    def apply_raw(self, changes):
        offset = self.raw_form.value('offset')
        value, text = self.raw_form.value('value'), self.raw_form.value('bytes')
        if bool(value) == bool(text): raise ValueError('Enter either an integer or hex bytes.')
        if text: self.backend.call('patchBytes', offset=offset, text=text)
        else: self.backend.call('setNumber', offset=offset, type=self.raw_form.value('type'), value=value)

    def make_review(self):
        layout = self.page('review', 'Review & export', 'Export creates a copy. Keep your backup; a correct checksum does not guarantee in-game acceptance.')
        self.review_text = QPlainTextEdit(); self.review_text.setReadOnly(True); layout.addWidget(self.review_text, 1)
        options = QFormLayout()
        self.export_platform = QComboBox(); combo_options(self.export_platform, [('Keep source format', 'keep'), ('PC (experimental if converting)', 'pc'), ('Switch (experimental if converting)', 'switch')], 'keep'); options.addRow('Output platform', self.export_platform)
        self.conversion_consent = QCheckBox('I accept experimental PC ↔ Switch conversion'); options.addRow(self.conversion_consent)
        self.repair_consent = QCheckBox('Repair an invalid original checksum (does not recover damaged data)'); options.addRow(self.repair_consent)
        self.export_gender = QComboBox(); combo_options(self.export_gender, [('Keep edited gender', 'keep'), ('Match original gender', 'original'), ('Male · Lest', 'male'), ('Female · Frey', 'female')], 'keep'); options.addRow('Gender on export', self.export_gender)
        self.reset_appearance = QCheckBox('Also reset appearance, portrait and outfit'); options.addRow(self.reset_appearance)
        layout.addLayout(options)
        row = QHBoxLayout()
        for label, callback in [('Download original backup', self.original_file), ('Download change report', self.report_file), ('Restore original in memory', lambda: self.mutate('reset')), ('Export edited save', self.export_file)]:
            button = QPushButton(label); button.clicked.connect(callback); row.addWidget(button)
        layout.addLayout(row)
        def render():
            state = self.backend.state()
            if not state:
                self.review_text.setPlainText('Open a save first.'); return
            changes = self.backend.call('changes')
            lines = [f'{state["name"]} · {state["changedBytes"]:,} changed bytes · {state["undo"]} undoable edits', 'Drafts pending: ' + ('YES — export blocked' if self.pending() else 'none')]
            lines += [f'0x{entry["offset"]:05X}: {bytes(entry["before"][:24]).hex(" ")} → {bytes(entry["after"][:24]).hex(" ")}' for entry in changes[:100]]
            if len(changes) > 100: lines.append(f'First 100 of {len(changes)} ranges shown; the JSON report includes all.')
            self.review_text.setPlainText('\n'.join(lines))
            slot = state['kind'] == 'slot'
            self.export_platform.setEnabled(slot); self.export_gender.setEnabled(slot); self.reset_appearance.setEnabled(slot); self.conversion_consent.setEnabled(slot)
        self.renderers['review'] = render

    def export_options(self):
        state = self.backend.state()
        if not state: raise ValueError('Open a save first.')
        slot = state['kind'] == 'slot'
        target = self.export_platform.currentData()
        gender = self.export_gender.currentData() if slot else 'keep'
        return {'platform': state['platform'] if not slot or target == 'keep' else target, 'experimental': self.conversion_consent.isChecked(), 'repair': self.repair_consent.isChecked(), 'gender': gender, 'resetAppearance': slot and self.reset_appearance.isChecked()}

    def export_bytes(self):
        if self.demo_mode: raise ValueError('Open a real save first. Synthetic demo export is disabled.')
        if self.pending(): raise ValueError('Apply or clear all drafts before exporting, including disabled editors.')
        return self.backend.build(**self.export_options())

    def write_file(self, path, data):
        file = QSaveFile(str(path))
        if not file.open(QIODevice.OpenModeFlag.WriteOnly): raise OSError(file.errorString())
        if file.write(data) != len(data) or not file.commit():
            file.cancelWriting(); raise OSError(file.errorString())

    def write_dialog(self, data, suggested, filter):
        filename, _ = QFileDialog.getSaveFileName(self, 'Save a new file — keep your backup', suggested, filter)
        if filename:
            self.write_file(filename, data)
            return True
        return False

    def export_file(self):
        def export():
            data = self.export_bytes()
            state = self.backend.state()
            filename = Path(state['name']).stem + '.edited.sav'
            if self.write_dialog(data, filename, 'RF4S save (*.sav)'):
                self.last_export = bytes(self.backend.call('working'))
                self.statusBar().showMessage('Edited save exported. Original source file was not automatically overwritten.', 10000)
        self.attempt(export)

    def original_file(self):
        def export():
            state = self.backend.state()
            if not state: raise ValueError('Open a save first.')
            self.write_dialog(bytes(self.backend.call('original')), Path(state['name']).stem + '.original.sav', 'RF4S save (*.sav)')
        self.attempt(export)

    def report_file(self):
        self.attempt(lambda: self.write_dialog(json.dumps({'application': 'RF4S native save editor', 'state': self.backend.state(), 'exportOptions': self.export_options(), 'changes': self.backend.call('changes')}, ensure_ascii=False, indent=2).encode('utf-8'), 'save.changes.json', 'Change report (*.json)'))

    def closeEvent(self, event):
        if self.closing or self.discard_confirmation(): event.accept()
        else: event.ignore()
