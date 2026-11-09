"""Native Qt Widgets save editor. No web views, HTML rendering or server."""
import json
import os
import re
from pathlib import Path

from PySide6.QtCore import Qt, QSignalBlocker, Signal, QSaveFile, QIODevice, QSettings, QLocale, QEvent, QSize, QAbstractListModel, QModelIndex, QRect
from PySide6.QtGui import QAction, QKeySequence, QPalette, QColor
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGridLayout, QLabel, QPushButton, QToolButton, QCheckBox, QLineEdit, QComboBox, QCompleter, QGroupBox,
    QScrollArea, QStackedWidget, QListWidget, QListView, QStyledItemDelegate, QStyle,
    QAbstractItemView, QFileDialog, QMessageBox, QPlainTextEdit, QSplitter, QSizePolicy, QTabWidget, QSpacerItem)

from native_save import NativeSave, local_references
from native_export import atomic_write, export_to_game_folder, game_save_directory
from native_icons import GameIcons
from native_i18n import UiLanguage, install_qt_translator
from native_layout import ResponsiveRow, wrapping_checkbox
from scripts.game_sources import all_references, LANGUAGES, NAME_TABLES, parse_name_table


def default_save_directory():
    appdata = os.environ.get('APPDATA')
    folder = Path(appdata) / 'Rune Factory 4 Special' if appdata else Path.home() / 'AppData' / 'Roaming' / 'Rune Factory 4 Special'
    return folder if folder.is_dir() else Path.home()


def system_ui_language(locale_name=None):
    return 'zh-CN' if (locale_name or QLocale.system().name()).lower().startswith('zh') else 'en'


class _ItemChoices(QAbstractListModel):
    """One indexed catalog per choice family; icons are requested only when drawn."""
    def __init__(self, choices, window):
        super().__init__(window)
        self.rows = list(choices)
        self.positions = {value: index for index, (_label, value) in enumerate(self.rows)}
        self.window = window

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid(): return None
        label, value = self.rows[index.row()]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole): return self.window.ui.text(label)
        if role == Qt.ItemDataRole.UserRole: return value
        if role == Qt.ItemDataRole.DecorationRole: return self.window.icons.icon('items', value)
        return None

    def index_for(self, value):
        if value not in self.positions:
            row = len(self.rows)
            self.beginInsertRows(QModelIndex(), row, row)
            self.positions[value] = row
            self.rows.append((f'Unrecognized stored ID {value}', value))
            self.endInsertRows()
        return self.positions[value]


class _InventoryRows(QAbstractListModel):
    """Saved-slot identity and lazy display data; never creates per-slot widgets."""
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.rows = []
        self.positions = {}

    def set_rows(self, rows):
        self.beginResetModel()
        self.rows = rows
        self.positions = {item['slot']: row for row, item in enumerate(rows)}
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid(): return None
        item = self.rows[index.row()]
        if role == Qt.ItemDataRole.UserRole: return item['slot']
        if role == Qt.ItemDataRole.UserRole + 1: return item
        if role == Qt.ItemDataRole.DecorationRole: return self.window.icons.icon('items', item['id'])
        name = self.window.item_name(item['id']) if item['id'] else self.window.ui.text('Empty')
        if role == Qt.ItemDataRole.DisplayRole: return name
        if role in (Qt.ItemDataRole.ToolTipRole, Qt.ItemDataRole.AccessibleTextRole):
            return f'{name}\n' + self.window.ui.text('Saved slot') + f' {item["slot"] + 1} · ' + self.window.ui.text('Quantity') + f' {item["quantity"]}\n' + self.window.ui.text('Levels') + ': ' + ', '.join(map(str, item['levels']))
        return None


class _ItemTile(QStyledItemDelegate):
    def sizeHint(self, option, index):
        return QSize(120, 128)

    def paint(self, painter, option, index):
        item = index.data(Qt.ItemDataRole.UserRole + 1)
        palette = index.model().window.palette()
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        tile = option.rect.adjusted(4, 4, -4, -4)
        painter.save()
        painter.setRenderHint(painter.RenderHint.Antialiasing)
        painter.setBrush(palette.highlight() if selected else palette.base())
        painter.setPen(palette.highlight().color() if selected else palette.mid().color())
        painter.drawRoundedRect(tile, 8, 8)
        index.data(Qt.ItemDataRole.DecorationRole).paint(painter, QRect(tile.center().x() - 28, tile.top() + 8, 56, 56))
        painter.setFont(option.font)
        painter.setPen(palette.highlightedText().color() if selected else palette.text().color())
        name = option.fontMetrics.elidedText(index.data(Qt.ItemDataRole.DisplayRole), Qt.TextElideMode.ElideRight, tile.width() - 12)
        painter.drawText(tile.adjusted(6, 67, -6, -24), Qt.AlignmentFlag.AlignCenter, name)
        painter.drawText(tile.adjusted(8, 0, -8, -5), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, f'Lv{item["level"]}' if item['id'] else '')
        painter.drawText(tile.adjusted(8, 0, -8, -5), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom, str(item['slot'] + 1))
        if item['quantity'] > 1:
            badge = QRect(tile.right() - 33, tile.top() + 5, 29, 24)
            painter.setBrush(palette.text()); painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(badge, 5, 5)
            painter.setPen(palette.base().color())
            painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, f'×{item["quantity"]}')
        if option.state & QStyle.StateFlag.State_HasFocus:
            painter.setBrush(Qt.BrushStyle.NoBrush); painter.setPen(palette.highlightedText().color())
            painter.drawRoundedRect(tile.adjusted(2, 2, -2, -2), 6, 6)
        painter.restore()


def combo_options(combo, choices, selected=None):
    with QSignalBlocker(combo):
        if isinstance(choices, _ItemChoices):
            if combo.model() is not choices: combo.setModel(choices)
            combo.setCurrentIndex(choices.index_for(selected))
            return
        combo.clear()
        for choice in choices:
            label, value = choice[:2]
            if len(choice) == 3: combo.addItem(choice[2], str(label), value)
            else: combo.addItem(str(label), value)
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
        self.labels = {}
        self.grid_mode = None
        self.base = {}
        self.drafts = {}
        self.syncing = False
        layout = QVBoxLayout(self)
        self.allow = QCheckBox('Enable editing')
        # Readiness is automatic. Retain this internal switch for existing test
        # harnesses, but there is no per-page opt-in checkbox in the interface.
        self.allow.setChecked(True)
        self.body = QWidget()
        self.grid = QGridLayout(self.body)
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(6)
        for index, field in enumerate(fields):
            key = field['key']
            label = QLabel(field.get('label', key))
            label.setWordWrap(True)
            self.labels[key] = label
            kind = field.get('kind', 'number')
            if kind == 'bool':
                control = QCheckBox()
                control.toggled.connect(lambda _value, key=key: self.track(key))
            elif kind == 'choice':
                control = QComboBox()
                control.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
                control.setMinimumContentsLength(12)
                control.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                if field.get('search'):
                    control.setEditable(True)
                    control.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
                    control.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
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
            self.grid.addWidget(label, index, 0)
            self.grid.addWidget(control, index, 1)
        self.body.installEventFilter(self)
        self.reflow()
        layout.addWidget(self.body)
        hint = QLabel(note)
        hint.setWordWrap(True)
        hint.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        hint.hide()
        self.setToolTip(note)
        footer = ResponsiveRow()
        self.status = QLabel('No draft')
        self.status.setWordWrap(True)
        footer.addWidget(self.status, 1)
        clear = QPushButton('Clear draft')
        clear.clicked.connect(self.clear)
        self.apply_button = QPushButton('Apply changes')
        self.apply_button.clicked.connect(self.applyRequested)
        footer.addWidget(clear)
        footer.addWidget(self.apply_button)
        layout.addWidget(footer)
        self.allow.toggled.connect(self.enabled_changed)
        self.set_ready(False)

    def eventFilter(self, watched, event):
        if watched is self.body and event.type() in (QEvent.Type.Resize, QEvent.Type.LayoutRequest, QEvent.Type.FontChange):
            self.reflow()
        return super().eventFilter(watched, event)

    def reflow(self):
        margins = self.grid.contentsMargins()
        width = self.body.width() - margins.left() - margins.right()
        label_width = max((label.fontMetrics().horizontalAdvance(label.text()) for label in self.labels.values()), default=0)
        control_width = max(150, self.fontMetrics().horizontalAdvance('0' * 16) + 40)
        group_width = label_width + control_width + self.grid.horizontalSpacing()
        columns = 2 if len(self.fields) > 12 and width >= group_width * 2 + 12 else 1
        above = columns == 1 and width < group_width
        mode = columns, above
        if self.grid_mode == mode: return
        self.grid_mode = mode
        for widget in [*self.labels.values(), *self.controls.values()]: self.grid.removeWidget(widget)
        for column in range(4): self.grid.setColumnStretch(column, 0)
        for column in range(columns): self.grid.setColumnStretch(column * 2 if above else column * 2 + 1, 1)
        rows = (len(self.fields) + columns - 1) // columns
        for index, key in enumerate(self.fields):
            column = index // rows * 2
            row = index % rows
            if above:
                self.grid.addWidget(self.labels[key], row * 2, 0)
                self.grid.addWidget(self.controls[key], row * 2 + 1, 0)
            else:
                self.grid.addWidget(self.labels[key], row, column)
                self.grid.addWidget(self.controls[key], row, column + 1)

    def enabled_changed(self):
        self.body.setEnabled(self.allow.isEnabled() and self.allow.isChecked())
        self.apply_button.setEnabled(self.allow.isEnabled() and self.allow.isChecked())
        self.draftChanged.emit()

    def set_ready(self, ready):
        if self.allow.isEnabled() == ready: return
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
        text = 'Pending edit · saved on export' if self.drafts else 'No draft'
        ui = getattr(self.window(), 'ui', None)
        if ui: ui.set_text(self.status, text)
        else: self.status.setText(text)
        self.draftChanged.emit()

    def write(self, key, value):
        control = self.controls[key]
        with QSignalBlocker(control):
            if isinstance(control, QCheckBox):
                control.setChecked(bool(value))
            elif isinstance(control, QComboBox):
                index = control.model().index_for(value) if isinstance(control.model(), _ItemChoices) else control.findData(value)
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
                typed = control.currentText() if isinstance(control, QComboBox) and control.isEditable() and key in self.drafts and control.currentText() != control.itemText(control.currentIndex()) else None
                if choices and key in choices:
                    combo_options(control, choices[key], current)
                self.base[key] = values.get(key)
                self.write(key, current)
                if typed is not None:
                    with QSignalBlocker(control): control.setEditText(typed)
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
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseStyleSheetPropagationInWidgetStyles, True)
        if QApplication.style().objectName().lower() != 'fusion': QApplication.setStyle('Fusion')
        font = self.font(); font.setPointSize(max(12, font.pointSize()))
        QApplication.setFont(font)
        self.setFont(font)
        palette = self.palette()
        for role, color in [(QPalette.ColorRole.Window, '#2e3440'), (QPalette.ColorRole.WindowText, '#eceff4'),
                            (QPalette.ColorRole.Base, '#2e3440'), (QPalette.ColorRole.Text, '#eceff4'),
                            (QPalette.ColorRole.Button, '#434c5e'), (QPalette.ColorRole.ButtonText, '#eceff4'),
                            (QPalette.ColorRole.Highlight, '#88c0d0'), (QPalette.ColorRole.HighlightedText, '#2e3440'),
                            (QPalette.ColorRole.Mid, '#4c566a'), (QPalette.ColorRole.AlternateBase, '#3b4252'),
                            (QPalette.ColorRole.Light, '#4c566a'), (QPalette.ColorRole.Midlight, '#434c5e'),
                            (QPalette.ColorRole.Dark, '#2e3440'), (QPalette.ColorRole.Shadow, '#2e3440'),
                            (QPalette.ColorRole.ToolTipBase, '#3b4252'), (QPalette.ColorRole.ToolTipText, '#eceff4'),
                            (QPalette.ColorRole.Link, '#88c0d0'), (QPalette.ColorRole.LinkVisited, '#b48ead'),
                            (QPalette.ColorRole.PlaceholderText, '#a6afbe')]:
            palette.setColor(role, QColor(color))
        for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
            palette.setColor(QPalette.ColorGroup.Disabled, role, QColor('#a6afbe'))
        QApplication.setPalette(palette)
        self.setPalette(palette)
        self.setStyleSheet('''
            QWidget { color: #eceff4; }
            QScrollArea { border: none; background: #2e3440; }
            QWidget#editorPage { background: #2e3440; }
            QToolBar { border: none; spacing: 6px; background: #3b4252; }
            QToolButton { padding: 6px; border-radius: 5px; }
            QToolButton:hover { background: #4c566a; }
            QToolButton#learnAllRecipes { background: #88c0d0; color: #2e3440; padding: 8px 12px; }
            QToolButton#learnAllRecipes:disabled { background: #434c5e; color: #a6afbe; }
            QAbstractItemView { background: #2e3440; color: #eceff4; selection-background-color: #88c0d0; selection-color: #2e3440; }
            QMenu, QToolTip { background: #3b4252; color: #eceff4; border: 1px solid #4c566a; }
            QMenu::item:selected { background: #88c0d0; color: #2e3440; }
            QListWidget#navigation { background: #3b4252; color: #eceff4; border: none; padding: 4px; }
            QListWidget#navigation::item { padding: 9px 6px; border-radius: 5px; }
            QListWidget#navigation::item:selected { background: #88c0d0; color: #2e3440; }
            QListWidget#navigation::item:disabled { color: #a6afbe; }
            QListView#inventoryGrid { background: #3b4252; border: 2px solid #4c566a; border-radius: 10px; }
            QLineEdit, QComboBox, QPlainTextEdit { background: #2e3440; color: #eceff4; border: 1px solid #4c566a; border-radius: 5px; padding: 4px 7px; }
            QLineEdit, QComboBox { min-height: 28px; }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #88c0d0; }
            QLineEdit:disabled, QComboBox:disabled { color: #a6afbe; background: #3b4252; }
            QPushButton { background: #434c5e; color: #eceff4; border: 1px solid #4c566a; border-radius: 6px; padding: 6px 10px; min-height: 24px; }
            QPushButton:hover { background: #4c566a; border-color: #88c0d0; }
            QPushButton:disabled { color: #a6afbe; background: #3b4252; }
            QGroupBox { border: 1px solid #4c566a; border-radius: 8px; margin-top: 14px; padding-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
            QTabBar::tab { background: #3b4252; padding: 7px 12px; border: 1px solid #4c566a; }
            QTabBar::tab:selected { background: #2e3440; color: #88c0d0; }
            QSplitter::handle { background: #4c566a; }
        ''')
        self.settings = QSettings('RF4S Save Editor', 'Native')
        self.ui_language_mode = self.settings.value('uiLanguageMode', 'auto')
        if self.ui_language_mode not in ('auto', 'en', 'zh-CN'): self.ui_language_mode = 'auto'
        self.ui = UiLanguage(system_ui_language() if self.ui_language_mode == 'auto' else self.ui_language_mode)
        self.qt_translator = install_qt_translator(self.ui, self)
        self.backend = NativeSave()
        self.icons = GameIcons()
        self.constants = self.backend.constants
        self.languages = {}
        self.language = 'en'
        self.item_names = {}
        self.inventory_choices = None
        self.inventory_rows_key = None
        self.inventory_view_key = None
        self.inventory_items = []
        self.source_path = None
        self.closing = False
        self.demo_mode = False
        self.forms = []
        self.renderers = {}
        self.pages = {}
        self.inventory_container = 'bag'
        self.inventory_slot = 0
        self.candidate = 1
        self.selections = {'skills': 0, 'friendship': 1, 'relationships': 1, 'people': 1, 'monsters': None, 'recipes': None, 'trophies': None, 'flags': None}
        self.setWindowTitle('Rune Factory 4 Special · Native save editor')
        self.resize(1160, 850)
        self.setMinimumSize(640, 480)
        toolbar = self.addToolBar('Save and references')
        self.save_toolbar = toolbar
        toolbar.setMovable(False)
        for title, callback, shortcut in [('Open save', self.open_file, QKeySequence.StandardKey.Open), ('Undo', lambda: self.mutate('undo'), QKeySequence.StandardKey.Undo), ('Redo', lambda: self.mutate('redo'), QKeySequence.StandardKey.Redo)]:
            action = QAction(title, self)
            action.triggered.connect(callback)
            if shortcut:
                action.setShortcut(QKeySequence(shortcut))
            toolbar.addAction(action)
            if title == 'Undo': self.undo_action = action
            if title == 'Redo': self.redo_action = action
        self.addToolBarBreak()
        toolbar = self.addToolBar('Interface and game names')
        toolbar.setMovable(False)
        toolbar.addWidget(QLabel('Interface: '))
        self.ui_language_combo = QComboBox()
        self.ui_language_combo.setMinimumWidth(80)
        self.ui_language_combo.setMaximumWidth(180)
        combo_options(self.ui_language_combo, [('Follow system', 'auto'), ('English', 'en'), ('简体中文', 'zh-CN')], self.ui_language_mode)
        self.ui_language_combo.currentIndexChanged.connect(self.select_ui_language)
        toolbar.addWidget(self.ui_language_combo)
        toolbar.addWidget(QLabel('Game names: '))
        self.language_combo = QComboBox()
        self.language_combo.setMinimumWidth(80)
        self.language_combo.setMaximumWidth(180)
        self.language_combo.setProperty('gameNames', True)
        self.language_combo.currentIndexChanged.connect(self.select_language)
        toolbar.addWidget(self.language_combo)
        self.export_action = QAction('Export edited save', self)
        self.export_action.setShortcut(QKeySequence.StandardKey.Save)
        self.export_action.triggered.connect(self.export_file)
        self.save_toolbar.addAction(self.export_action)
        splitter = QSplitter()
        self.splitter = splitter
        self.compact_navigation = None
        self.navigation = QListWidget()
        self.navigation.setObjectName('navigation')
        self.navigation.setMinimumWidth(110)
        self.navigation.setMaximumWidth(210)
        self.navigation.setWordWrap(True)
        self.navigation.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.navigation.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.stack = QStackedWidget()
        splitter.addWidget(self.navigation)
        splitter.addWidget(self.stack)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)
        self.make_overview()
        self.make_calendar()
        self.make_player()
        self.make_player_name()
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
        self.ui.apply(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, 'splitter'): return
        if hasattr(self, 'inventory_grid'):
            self.inventory_grid.setFixedHeight(140 if self.height() < 600 else 268)
        compact = self.width() < 900
        if compact != self.compact_navigation:
            self.compact_navigation = compact
            width = 140 if compact else 210
            self.navigation.setMaximumWidth(width)
            self.splitter.setSizes([width, max(0, self.width() - width)])

    def select_ui_language(self):
        self.ui_language_mode = self.ui_language_combo.currentData() or 'auto'
        self.ui.code = system_ui_language() if self.ui_language_mode == 'auto' else self.ui_language_mode
        self.settings.setValue('uiLanguageMode', self.ui_language_mode)
        self.ui.apply(self)
        if self.inventory_choices:
            for model in self.inventory_choices.values():
                model.dataChanged.emit(model.index(0), model.index(model.rowCount() - 1))
        # Keep controls intact, including half-typed values and disabled drafts.
        current = next((key for key, (_widget, _layout, index) in self.pages.items() if index == self.stack.currentIndex()), None)
        if current == 'inventory': self.render_item_preview()
        elif current in ('flags', 'review', 'relationships', 'player-name'):
            self.renderers[current]()
            self.ui.apply(self.pages[current][0])

    def page(self, key, title, note=''):
        widget = QWidget()
        widget.setObjectName('editorPage')
        layout = QVBoxLayout(widget)
        heading = QLabel(title)
        font = heading.font(); font.setPointSize(20); font.setBold(True); heading.setFont(font)
        layout.addWidget(heading)
        if note: heading.setToolTip(note)
        self.pages[key] = (widget, layout, self.navigation.count())
        self.navigation.addItem(title)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(widget)
        self.stack.addWidget(scroll)
        return layout

    def form(self, layout, fields, callback, note=''):
        form = EditForm(fields, note)
        form.apply_callback = callback
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
        self.statusBar().showMessage(self.ui.text('Changes applied in memory. Review and export; the original is untouched.'), 10000)

    def apply_all_drafts(self):
        pending = [form for form in self.forms if form.drafts]
        callbacks = [lambda form=form: form.apply_callback(form.changes()) for form in pending]
        if callbacks: self.backend.apply_callbacks(callbacks)
        for form in pending:
            form.drafts.clear(); form.status.setText(self.ui.text('No draft'))
        if pending: self.refresh()

    def attempt(self, action):
        try:
            return action()
        except (ValueError, OSError, KeyError) as error:
            self.statusBar().showMessage(self.ui.text(str(error)))
            if not getattr(self, 'testing', False):
                QMessageBox.warning(self, self.ui.text('Edit not applied'), self.ui.text(str(error)))
            else:
                self.test_errors.append(str(error))

    def pending(self):
        return any(form.drafts for form in self.forms)

    def update_export(self):
        state = self.backend.state()
        self.export_action.setEnabled(bool(state) and not self.demo_mode)
        self.export_action.setToolTip(self.ui.text('Save pending edits to the game folder and create a backup.'))
        if not state: text = 'No save loaded'
        elif self.demo_mode: text = 'Demo · export disabled'
        elif self.pending(): text = 'Pending edit · saved on export'
        else:
            text = {'original': 'Original loaded · no edits', 'unexported': 'Unexported changes', 'exported': 'Current edits exported'}[state['exportState']]
        self.ui.set_text(self.document_status, text)

    def select_page(self, index):
        if index < 0:
            return
        self.stack.setCurrentIndex(index)
        self.refresh_page()

    def refresh_page(self):
        for key, (_widget, _layout, index) in self.pages.items():
            if index == self.stack.currentIndex() and key in self.renderers:
                self.attempt(self.renderers[key])
                self.ui.apply(self.pages[key][0])

    def refresh(self):
        state = self.backend.state()
        self.undo_action.setEnabled(bool(state and state['undo']))
        self.redo_action.setEnabled(bool(state and state['redo']))
        slot = bool(state and state['kind'] == 'slot')
        self.learn_all_recipes_action.setEnabled(slot and bool(self.backend.call('recipes')))
        always = {'overview', 'reference', 'review', 'player-name'}
        for key, (_widget, _layout, index) in self.pages.items():
            available = key in always or bool(state) and (key in {'raw'} or slot and key != 'system' or not slot and key == 'system')
            if key in {'player', 'inventory'}: available = slot
            item = self.navigation.item(index)
            item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled if available else Qt.ItemFlag.NoItemFlags)
        self.overview_status.setText('No save loaded' if not state else f'{state["name"]}\n{state["platform"].upper()} · {state["size"]:,} bytes · CRC {"valid" if state["crcValid"] else "mismatch — rebuilt on export"}\n{state["changedBytes"]:,} changed bytes · {state["undo"]} undoable edits')
        self.refresh_page()
        self.update_export()

    def mutate(self, operation, **args):
        self.attempt(lambda: self.backend.call(operation, **args))
        self.refresh()

    def open_bytes(self, data, name, path=None, demo=False):
        self.backend.open(data, name)
        self.inventory_rows_key = None
        self.source_path = path
        self.demo_mode = demo
        self.export_platform.setCurrentIndex(self.export_platform.findData('keep'))
        self.export_gender.setCurrentIndex(self.export_gender.findData('keep'))
        self.conversion_consent.setChecked(False)
        self.repair_consent.setChecked(False)
        self.reset_appearance.setChecked(False)
        self.reset_dating.setChecked(False)
        for form in self.forms:
            form.drafts.clear(); form.base.clear(); form.allow.setChecked(True)
        filename = Path(name).name.lower()
        target = filename if re.fullmatch(r'rf4_s\d{2}\.sav|rf4_sys\.sav', filename) else 'rf4_sys.sav' if self.backend.state()['kind'] == 'system' else None
        with QSignalBlocker(self.target_save_combo): self.target_save_combo.setCurrentIndex(self.target_save_combo.findData(target))
        self.inventory_container = 'bag'; self.inventory_slot = 0
        self.candidate = 1
        self.refresh()

    def question(self, title, text, buttons, default):
        dialog = QMessageBox(QMessageBox.Icon.Question, self.ui.text(title), self.ui.text(text), buttons, self)
        dialog.setDefaultButton(default)
        # QMessageBox sizes itself from the body/buttons, ignoring its title.
        # A layout spacer also survives Qt's internal fixed-size calculation.
        width = max(360, dialog.fontMetrics().horizontalAdvance(dialog.windowTitle()) + 120)
        grid = dialog.layout()
        grid.addItem(QSpacerItem(width, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum),
                     grid.rowCount(), 0, 1, grid.columnCount())
        try:
            return dialog.exec()
        finally:
            dialog.deleteLater()

    def discard_confirmation(self):
        state = self.backend.state()
        if not self.pending() and not (state and state['exportState'] == 'unexported'):
            return True
        return self.question('Unexported changes', 'Discard unexported edits and drafts?', QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel) == QMessageBox.StandardButton.Discard

    def open_file(self):
        if not self.discard_confirmation(): return
        folder = self.source_path.parent if self.source_path else default_save_directory()
        filename, _ = QFileDialog.getOpenFileName(self, self.ui.text('Open a slot or system save'), str(folder), 'RF4S saves (*.sav)')
        if filename:
            self.attempt(lambda: self.open_bytes(Path(filename).read_bytes(), Path(filename).name, Path(filename)))

    def make_overview(self):
        layout = self.page('overview', 'Save overview', 'Native desktop controls · offline · no browser or local server. Back up your save folder and close the game before editing.')
        self.document_status = QLabel(); self.document_status.setWordWrap(True); layout.addWidget(self.document_status)
        self.overview_status = QLabel(); self.overview_status.setWordWrap(True); self.overview_status.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred); layout.addWidget(self.overview_status)
        for title, callback in [('Open save', self.open_file), ('Reload game references (optional)', self.read_game), ('Read extracted item tables', lambda: self.read_tables('importItems')), ('Read extracted recipe tables', lambda: self.read_tables('importRecipes')), ('Read extracted language names', self.read_languages)]:
            button = QPushButton(title); button.clicked.connect(callback); layout.addWidget(button)
        layout.addStretch()

    def demo(self):
        if self.discard_confirmation():
            self.open_bytes(bytes(self.backend.call('demoBytes')), 'Synthetic demo.sav (not playable; export disabled)', demo=True)

    def load_references(self, data):
        if self.pending(): self.apply_all_drafts()
        self.backend.call('references', items=data.get('items'), recipes=data.get('recipes'))
        self.languages = (data.get('languages') or {}).get('languages', {})
        if 'icons' in data: self.icons.load_index(data['icons'])
        self.item_names = {item['id']: item['name'] for item in self.backend.call('items')}
        self.update_languages()

    def read_game(self):
        if self.pending():
            try: self.apply_all_drafts()
            except ValueError as error: self.statusBar().showMessage(self.ui.text(str(error))); return
        folder = QFileDialog.getExistingDirectory(self, self.ui.text('Choose game folder containing Bundle'))
        if folder:
            self.attempt(lambda: self.load_references(all_references(folder)))
            self.refresh()

    def read_tables(self, operation):
        if self.pending():
            try: self.apply_all_drafts()
            except ValueError as error: self.statusBar().showMessage(self.ui.text(str(error))); return
        paths, _ = QFileDialog.getOpenFileNames(self, self.ui.text('Read extracted definition tables'), '', 'Game tables (*.bin)')
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
                self.inventory_choices = None
                self.inventory_rows_key = None
            self.attempt(load); self.refresh()

    def read_languages(self):
        paths, _ = QFileDialog.getOpenFileNames(self, self.ui.text('Read extracted name tables'), '', 'Game names (*.eng *.jpn *.fra *.deu *.kor *.twn *.chn)')
        def load():
            staged = {key: dict(value) for key, value in self.languages.items()}
            if len(paths) > 28: raise ValueError('Read up to 28 name tables.')
            for filename in paths:
                path = Path(filename)
                parts = path.name.split('.')
                if len(parts) != 2 or parts[1] not in LANGUAGES: raise ValueError('Choose supported game TEXT name tables.')
                kind = NAME_TABLES.get(parts[0])
                if not kind or path.stat().st_size > 16 * 1024 * 1024: raise ValueError('Choose name tables, not descriptions.')
                code, label = LANGUAGES[parts[1]]
                staged.setdefault(code, {'label': label})[kind] = parse_name_table(kind, path.read_bytes())
            self.languages = staged; self.update_languages(); self.refresh()
        if paths: self.attempt(load)

    def update_languages(self):
        self.inventory_choices = None
        self.inventory_rows_key = None
        choices = [('English', 'en')] + [(entry['label'], code) for code, entry in self.languages.items() if code != 'en']
        if self.language not in {code for _label, code in choices}: self.language = 'en'
        combo_options(self.language_combo, choices, self.language)

    def select_language(self):
        self.language = self.language_combo.currentData() or 'en'
        self.inventory_choices = None
        self.refresh_page()

    def name(self, kind, index, fallback):
        names = self.languages.get(self.language, {}).get(kind, [])
        return names[index] if 0 <= index < len(names) and names[index] else fallback

    def item_name(self, index):
        return self.name('items', index, self.item_names.get(index, f'Unknown item {index}'))

    def person_name(self, index):
        fallback = self.constants['people'][index]
        return fallback if index in (22, 23) else self.name('people', index, fallback)

    def icon_choices(self, choices, kind):
        return [(label, value, self.icons.icon(kind, value)) for label, value in choices]

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
            state = self.backend.state(); ready = bool(state and state['kind'] == 'slot'); self.player_form.set_ready(ready)
            if ready: self.player_form.set_data(self.backend.call('player'))
        self.renderers['player'] = render

    def make_player_name(self):
        layout = self.page('player-name', 'Player name', 'Player names are stored in rf4_sys.sav, not individual slot files. Select the matching bank and save slot. Editing a name does not create a slot or change its gender.')
        self.name_record = 0
        self.player_name_selector = QComboBox(); self.player_name_selector.setProperty('gameNames', True)
        layout.addWidget(self.player_name_selector)
        self.player_name_info = QLabel(); self.player_name_info.setWordWrap(True)
        self.player_name_info.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.player_name_info)
        self.player_name_form = self.form(layout, [{'key': 'name', 'label': 'Player name (up to 6 characters / 18 UTF-8 bytes)', 'kind': 'text'}],
            lambda changes: self.backend.call('setPlayerName', id=self.name_record, name=changes['name']),
            'Blank uses the game default on the next load. Unsupported font glyphs may not display. Reset only prepares a draft; click Apply changes, then export the system save.')
        self.reset_player_name_button = QPushButton('Reset player name to game default')
        def reset_draft():
            self.player_name_form.write('name', '')
            self.player_name_form.track('name')
        self.reset_player_name_button.clicked.connect(reset_draft)
        layout.insertWidget(layout.count() - 1, self.reset_player_name_button)
        self.player_name_form.draftChanged.connect(lambda: self.reset_player_name_button.setEnabled(
            self.player_name_form.allow.isEnabled() and self.player_name_form.allow.isChecked()))
        self.reset_player_name_button.setEnabled(False)
        self.player_name_selector.currentIndexChanged.connect(self.change_name_record)
        self.renderers['player-name'] = self.render_player_name

    def change_name_record(self):
        selected = self.player_name_selector.currentData()
        if selected is None or selected == self.name_record: return
        if self.player_name_form.drafts:
            try: self.apply_form(self.player_name_form, self.player_name_form.apply_callback)
            except ValueError as error:
                with QSignalBlocker(self.player_name_selector): self.player_name_selector.setCurrentIndex(self.player_name_selector.findData(self.name_record))
                self.statusBar().showMessage(self.ui.text(str(error))); return
        with QSignalBlocker(self.player_name_selector): self.player_name_selector.setCurrentIndex(self.player_name_selector.findData(selected))
        self.name_record = selected
        self.render_player_name()

    def render_player_name(self):
        state = self.backend.state()
        ready = bool(state and state['kind'] == 'system')
        self.player_name_selector.setEnabled(ready)
        if not ready:
            self.player_name_form.set_ready(False)
            self.ui.set_text(self.player_name_info, 'Open rf4_sys.sav to edit player names. Individual slot files do not contain this field.')
            with QSignalBlocker(self.player_name_selector): self.player_name_selector.clear()
            return
        records = self.backend.call('playerNames')
        choices = []
        for record in records:
            text = record['name'] or self.ui.text('[Game default]') if record['present'] else self.ui.text('[Empty slot]')
            choices.append((self.ui.text(f'Bank {record["bank"] + 1} · slot {record["slot"]:02d}') + ' · ' + text, record['id']))
        combo_options(self.player_name_selector, choices, self.name_record)
        record = records[self.name_record]
        self.player_name_form.set_ready(record['present'])
        self.player_name_form.set_data({'name': record['name']})
        self.ui.set_text(self.player_name_info, 'Select an existing save-slot name record; this does not create a save.' if not record['present']
                         else 'Stored name bytes are unrecognized; keep unless intentionally replacing.' if not record['valid']
                         else 'Reset leaves the name empty so the game chooses its default from the loaded character gender and game language.')

    def make_inventory(self):
        layout = self.page('inventory', 'Bag & storage', 'Saved slots do not unlock capacity. Replacements clear previous metadata. Element changes append crystals without deleting existing upgrades; test equipment edits in-game.')
        top = ResponsiveRow()
        self.container_combo = QComboBox()
        combo_options(self.container_combo, [(spec['label'], key) for key, spec in self.constants['inventories'].items()], 'bag')
        self.container_combo.currentIndexChanged.connect(self.change_container)
        self.inventory_search = QLineEdit(); self.inventory_search.setPlaceholderText('Filter saved items by name or slot')
        self.inventory_search.textChanged.connect(self.render_inventory_grid)
        self.all_slots = QCheckBox('Show empty slots'); self.all_slots.setChecked(True); self.all_slots.toggled.connect(self.render_inventory_grid)
        top.addWidget(self.container_combo); top.addWidget(self.inventory_search, 1); top.addWidget(self.all_slots)
        layout.addWidget(top)
        self.inventory_grid = QListView()
        self.inventory_grid.setObjectName('inventoryGrid')
        self.inventory_model = _InventoryRows(self)
        self.inventory_grid.setModel(self.inventory_model)
        self.inventory_grid.setItemDelegate(_ItemTile(self.inventory_grid))
        self.inventory_grid.setViewMode(QListView.ViewMode.IconMode)
        self.inventory_grid.setResizeMode(QListView.ResizeMode.Adjust)
        self.inventory_grid.setMovement(QListView.Movement.Static)
        self.inventory_grid.setUniformItemSizes(True)
        self.inventory_grid.setGridSize(QSize(120, 128))
        self.inventory_grid.setIconSize(QSize(56, 56))
        self.inventory_grid.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.inventory_grid.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.inventory_grid.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.inventory_grid.setFixedHeight(268)
        self.inventory_grid.selectionModel().currentChanged.connect(self.change_inventory_slot)
        layout.addWidget(self.inventory_grid)
        self.slot_label = QLabel(); self.slot_label.setWordWrap(True); self.slot_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.slot_icon = QLabel(); self.slot_icon.setFixedSize(64, 64)
        font = self.slot_label.font(); font.setPointSize(14); font.setBold(True); self.slot_label.setFont(font)
        slot_row = QHBoxLayout(); slot_row.addWidget(self.slot_icon); slot_row.addWidget(self.slot_label, 1); layout.addLayout(slot_row)
        preview = QGroupBox('Item effect preview'); preview_row = QVBoxLayout(preview)
        preview.setCheckable(True); preview.setChecked(True)
        preview.setToolTip('Uncheck to hide the preview and make more room for item fields.')
        self.item_preview_tabs = QTabWidget()
        preview_row.addWidget(self.item_preview_tabs)
        self.item_preview_before = QPlainTextEdit(); self.item_preview_after = QPlainTextEdit()
        for panel in (self.item_preview_before, self.item_preview_after):
            panel.setReadOnly(True); panel.setMaximumHeight(160)
        self.item_preview_tabs.addTab(self.item_preview_before, 'Current item')
        self.item_preview_tabs.addTab(self.item_preview_after, 'Draft result')
        self.item_preview_tabs.setCurrentIndex(1)
        preview.toggled.connect(self.item_preview_tabs.setVisible)
        layout.addWidget(preview)
        fields = [{'key': 'id', 'label': 'Item (type to search)', 'kind': 'choice', 'search': True}, {'key': 'quantity', 'label': 'Quantity'}, {'key': 'level', 'label': 'Set all item levels', 'optional': True}, {'key': 'element', 'label': 'Weapon / tool element', 'kind': 'choice', 'choices': [('Keep existing', None)] + [(item['name'], item['value']) for item in self.constants['elements']]}, {'key': 'inherited', 'label': 'Inherited equipment', 'kind': 'choice', 'search': True}, {'key': 'totalLevel', 'label': 'Total-level bonus (0–150)'}, {'key': 'rarityBonus', 'label': 'Rarity bonus (0–200)'}, *[{'key': f'craft{i}', 'label': f'Crafting attachment {i + 1}', 'kind': 'choice', 'search': True} for i in range(3)], *[{'key': f'upgrade{i}', 'label': f'Upgrade {i + 1} · level {i + 2}', 'kind': 'choice', 'search': True} for i in range(9)]]
        self.inventory_form = self.form(layout, fields, self.apply_inventory, 'Attachment IDs are 10-bit (0–1023), equipment only. Unchanged fields are preserved; 0 removes an attachment. Blank level preserves mixed unit levels.')
        for control in self.inventory_form.controls.values():
            if isinstance(control, QComboBox):
                control.setIconSize(QSize(40, 40))
                control.view().setIconSize(QSize(40, 40))
                control.view().setUniformItemSizes(True)
                if control.isEditable():
                    control.completer().popup().setIconSize(QSize(40, 40))
                    control.completer().popup().setUniformItemSizes(True)
                if control is not self.inventory_form.controls['element']: control.setProperty('gameNames', True)
        self.inventory_form.controls['id'].currentIndexChanged.connect(self.inventory_id_changed)
        self.inventory_form.draftChanged.connect(self.render_item_preview)
        self.renderers['inventory'] = self.render_inventory

    def change_container(self):
        selected = self.container_combo.currentData()
        if self.inventory_form.drafts:
            try: self.apply_form(self.inventory_form, self.apply_inventory)
            except ValueError as error:
                with QSignalBlocker(self.container_combo): self.container_combo.setCurrentIndex(self.container_combo.findData(self.inventory_container))
                self.statusBar().showMessage(self.ui.text(str(error))); return
        self.inventory_container = selected; self.inventory_slot = 0; self.render_inventory()

    def change_inventory_slot(self):
        selected = self.inventory_grid.currentIndex()
        if not selected.isValid(): return
        slot = selected.data(Qt.ItemDataRole.UserRole)
        if slot == self.inventory_slot: return
        if self.inventory_form.drafts:
            try: self.apply_form(self.inventory_form, self.apply_inventory)
            except ValueError as error:
                self.statusBar().showMessage(self.ui.text(str(error))); self.render_inventory_grid(); return
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

    def render_inventory_grid(self):
        state = self.backend.state()
        if not state or state['kind'] != 'slot': return
        key = self.backend.revision, self.inventory_container, self.language
        if self.inventory_rows_key != key:
            self.inventory_items = self.backend.call('inventory', container=self.inventory_container)
            self.inventory_rows_key = key
            self.inventory_view_key = None
        query = self.inventory_search.text().casefold().strip()
        view_key = key, query, self.all_slots.isChecked()
        with QSignalBlocker(self.inventory_grid.selectionModel()):
            if self.inventory_view_key != view_key:
                rows = [item for item in self.inventory_items if (item['id'] or self.all_slots.isChecked()) and (not query or query in f'{item["slot"] + 1} {self.item_name(item["id"])}'.casefold())]
                self.inventory_model.set_rows(rows)
                self.inventory_view_key = view_key
            row = self.inventory_model.positions.get(self.inventory_slot)
            self.inventory_grid.setCurrentIndex(self.inventory_model.index(row) if row is not None else QModelIndex())

    def render_inventory(self):
        state = self.backend.state(); ready = bool(state and state['kind'] == 'slot'); self.inventory_form.set_ready(ready)
        if not ready: return
        with QSignalBlocker(self.container_combo): self.container_combo.setCurrentIndex(self.container_combo.findData(self.inventory_container))
        self.render_inventory_grid()
        item = self.backend.call('item', container=self.inventory_container, slot=self.inventory_slot)
        retired_models = []
        if self.inventory_choices is None:
            retired_models = {control.model() for control in self.inventory_form.controls.values() if isinstance(control, QComboBox) and isinstance(control.model(), _ItemChoices)}
            available = self.backend.call('items', editableOnly=True)
            choices = sorted([(self.item_name(entry['id']), entry['id']) for entry in available], key=lambda choice: choice[0].casefold())
            self.inventory_choices = {
                'id': _ItemChoices([('Empty / clear slot · 0', 0)] + [(f'{label} · {value}', value) for label, value in choices], self),
                'attachment': _ItemChoices([('None / remove · 0', 0)] + [(f'{label} · {value}', value) for label, value in choices if value <= 1023], self),
                'inherited': _ItemChoices([('None · 0', 0)] + [(f'{self.item_name(entry["id"])} · {entry["id"]}', entry['id']) for entry in available if entry['id'] <= 1023 and entry['category'] in (15,16,17,18,19,24,25,26,27,28,29,30,31,32,33,34,35,36,37)], self),
            }
        options = {key: self.inventory_choices['attachment'] for key in self.inventory_form.controls if key.startswith(('craft', 'upgrade'))}
        options.update(id=self.inventory_choices['id'], inherited=self.inventory_choices['inherited'])
        self.inventory_form.set_data({'id': item['id'], 'quantity': item['quantity'], 'level': None, 'element': None, **item['details']}, options)
        for model in retired_models: model.deleteLater()
        self.slot_label.setText(f'Saved slot {self.inventory_slot + 1} · {self.item_name(item["id"])} · current element: {next((entry["name"] for entry in self.constants["elements"] if entry["value"] == item["element"]), "not recognized / not a weapon")}.')
        self.render_item_preview()
        self.ui.apply(self.pages['inventory'][0])

    def inventory_changes(self, changes):
        basic = {'id': self.inventory_form.value('id'), 'quantity': self.inventory_form.value('quantity')}
        if changes.get('level') not in (None, ''): basic['level'] = changes['level']
        details = {key: value for key, value in changes.items() if key not in {'id', 'quantity', 'level'} and value is not None}
        return basic, details

    def apply_inventory(self, changes):
        basic, details = self.inventory_changes(changes)
        self.backend.call('setItem', container=self.inventory_container, slot=self.inventory_slot, changes=basic, details=details)

    def effect_preview_text(self, title, preview):
        text = self.ui.text
        item = preview['item']
        lines = [text(title), f'{self.item_name(item["id"])} · ID {item["id"]} · Lv {item["level"]}', text('Definition-based preview, not final in-game stats.')]
        if item['element'] is not None:
            element = next((entry['name'] for entry in self.constants['elements'] if entry['value'] == item['element']), str(item['element']))
            lines.append(text('Weapon / tool element') + ': ' + text(element))
        for section in preview['sections']:
            lines += ['', text(section['title']) + ' · ' + self.item_name(section['id'])]
            if not section['available']:
                lines.append(text('Read your game equipment / use / upgrade tables to preview effects.'))
            elif not section['effects']:
                lines.append(text('No nonzero effects in this reference record.'))
            for effect in section['effects']:
                value = '' if effect['kind'] == 'flag' else str(round(effect['value'], 3)) if isinstance(effect['value'], (int, float)) else effect['value']
                lines.append(f'{text(effect["label"])}: {value}{text(effect["unit"])}' if value else text(effect['label']))
        lines += ['', *(text(note) for note in preview['notices']), text('Preview only — no save bytes or undo history are changed.')]
        return '\n'.join(lines)

    def render_item_preview(self):
        if not hasattr(self, 'inventory_form'): return
        state = self.backend.state()
        if not state or state['kind'] != 'slot':
            self.item_preview_before.clear(); self.item_preview_after.clear(); return
        try:
            form = self.inventory_form
            basic, details = self.inventory_changes(form.drafts) if form.drafts else ({}, {})
            self.slot_icon.setPixmap(self.icons.icon('items', basic.get('id', form.base.get('id', 0))).pixmap(64, 64))
            result = self.backend.call('previewItem', container=self.inventory_container, slot=self.inventory_slot, changes=basic, details=details)
            self.item_preview_before.setPlainText(self.effect_preview_text('Current item', result['before']))
            self.item_preview_after.setPlainText(self.effect_preview_text('Draft result', result['after']))
        except (ValueError, TypeError) as error:
            self.item_preview_after.setPlainText(self.ui.text('Preview unavailable') + ': ' + self.ui.text(str(error)))

    def make_record_pages(self):
        self.record_forms = {}
        self.record_selectors = {}
        specs = {
            'skills': ('Skills', [{'key': 'level', 'label': 'Skill level'}, {'key': 'xp', 'label': 'Experience (0–16,777,215)'}], 'Direct skill levels do not award stat gains. Crafting / resistance skills cap at 99; others at 999.'),
            'recipes': ('Learned recipes', [{'key': 'known', 'label': 'Recipe learned', 'kind': 'bool'}], 'Variants sharing a learned bit change together. Recipe difficulty is not stored as an editable save value.'),
            'friendship': ('Friendship', [{'key': 'level', 'label': 'Friendship level (0–10,000)'}], 'Does not trigger dating, wedding or story events.'),
            'relationships': ('Dating & nicknames', [
                {'key': 'dating', 'label': 'Dating status (marriage candidates only)', 'kind': 'bool'},
                {'key': 'npcCallsPlayer', 'label': 'NPC calls player', 'kind': 'choice'},
                {'key': 'playerCallsNpc', 'label': 'Player calls NPC', 'kind': 'choice'},
            ], 'Saved flags and nicknames only; does not simulate confessions, breakups, marriage or story events. Nicknames are independent of dating. Export dating cleanup, if enabled, overrides these fields for its targets. Guests are not supported here.'),
            'people': ('People stats', [{'key': key, **field} for key, field in self.constants['stats'].items()], 'Stored base stats only; no spawning or derived-stat recalculation.'),
            'monsters': ('Tamed monsters', [{'key': 'friendship', 'label': 'Friendship (0–1,000)'}, *[{'key': key, **field} for key, field in self.constants['stats'].items()]], 'Existing tamed monsters only. Names, species and barns are preserved.'),
            'trophies': ('Trophy records', [{'key': 'value', 'label': 'Recorded result', 'kind': 'choice'}], 'Recorded game results only, not physical trophies or Steam achievements.'),
        }
        for key, (title, fields, note) in specs.items():
            layout = self.page(key, title, note)
            selector = QComboBox()
            selector.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            selector.setMinimumContentsLength(12)
            selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            selector.setIconSize(QSize(40, 40))
            selector.setProperty('gameNames', key != 'trophies')
            layout.addWidget(selector)
            self.record_selectors[key] = selector
            if key == 'recipes':
                row = ResponsiveRow()
                self.recipe_group = QComboBox()
                combo_options(self.recipe_group, [('All groups', 'all')] + [(label, kind) for kind, label in self.constants['recipeGroups'].items()], 'all')
                self.recipe_search = QLineEdit(); self.recipe_search.setPlaceholderText('Filter recipe result names')
                self.recipe_group.currentIndexChanged.connect(self.filter_recipes)
                self.recipe_search.textChanged.connect(self.filter_recipes)
                row.addWidget(self.recipe_group); row.addWidget(self.recipe_search, 1); layout.addWidget(row)
                row = ResponsiveRow()
                self.learn_all_recipes_action = QAction('Learn all recipes', self)
                self.learn_all_recipes_action.setShortcut(QKeySequence('Ctrl+Shift+L'))
                self.learn_all_recipes_action.setToolTip('Learn all loaded recipes, ignoring filters (Ctrl+Shift+L).')
                self.learn_all_recipes_action.triggered.connect(lambda: self.attempt(lambda: self.bulk_recipes(True, all_recipes=True)))
                self.addAction(self.learn_all_recipes_action)
                self.learn_all_recipes_button = QToolButton()
                self.learn_all_recipes_button.setObjectName('learnAllRecipes')
                self.learn_all_recipes_button.setDefaultAction(self.learn_all_recipes_action)
                row.addWidget(self.learn_all_recipes_button)
                for title, known in [('Learn filtered recipes', True), ('Forget filtered recipes', False)]:
                    button = QPushButton(title); button.clicked.connect(lambda _checked=False, known=known: self.attempt(lambda: self.bulk_recipes(known))); row.addWidget(button)
                layout.addWidget(row)
            form = self.form(layout, fields, lambda changes, key=key: self.apply_record(key, changes))
            self.record_forms[key] = form
            if key == 'relationships':
                for field in ('npcCallsPlayer', 'playerCallsNpc'): form.controls[field].setProperty('gameNames', True)
                self.nickname_help = QLabel(); self.nickname_help.setWordWrap(True)
                self.nickname_help.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
                layout.insertWidget(2, self.nickname_help)
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
            try: self.apply_form(self.record_forms['recipes'], self.record_forms['recipes'].apply_callback)
            except ValueError as error: self.statusBar().showMessage(self.ui.text(str(error))); return
        self.render_record('recipes')

    def change_record(self, key):
        form = self.record_forms[key]
        selector = self.record_selectors[key]
        selected = selector.currentData()
        if selected == self.selections[key]: return
        if form.drafts:
            try: self.apply_form(form, form.apply_callback)
            except ValueError as error:
                with QSignalBlocker(selector): selector.setCurrentIndex(selector.findData(self.selections[key]))
                self.statusBar().showMessage(self.ui.text(str(error))); return
            with QSignalBlocker(selector): selector.setCurrentIndex(selector.findData(selected))
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
            elif key in ('friendship', 'relationships'): label, value = self.person_name(record['id']), record['id']
            elif key == 'people': label, value = record['name'], record['id']
            elif key == 'monsters': label, value = f'{record["id"] + 1} · {record["name"] or "Unnamed"} · species {record["species"]}', record['id']
            elif key == 'recipes': label, value = f'{self.item_name(record["result"])} · difficulty {record["level"]} · variant {record["index"]}', f'{record["kind"]}:{record["index"]}'
            else: label, value = record['label'], record['name']
            choices.append((label, value))
        if key in ('friendship', 'relationships', 'people'): choices = self.icon_choices(choices, 'people')
        elif key == 'recipes':
            choices = [(label, value, self.icons.icon('items', record['result'])) for (label, value), record in zip(choices, records)]
        selected = self.selections[key]
        if selected not in {choice[1] for choice in choices} and not form.drafts:
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
        elif key == 'relationships':
            values = record
            options = {field: self.nickname_choices(record, field) for field in ('npcCallsPlayer', 'playerCallsNpc')}
            self.ui.set_text(self.nickname_help, 'Nickname labels use Game names, not Interface. Player-name tokens appear as [Player name].' if self.nickname_names()
                             else 'Read game folder (or rf3TxtHeroNickName name tables) to load special nickname choices. Defaults and stored IDs remain available.')
        else: values = record
        form.set_data(values, options)
        if key == 'relationships': form.controls['dating'].setEnabled(record['canDate'])

    def nickname_names(self):
        return self.languages.get(self.language, {}).get('nicknames') or self.languages.get('en', {}).get('nicknames', [])

    def nickname_choices(self, record, field):
        names = self.nickname_names()
        choices = []
        for gender, caption in [('male', 'Default for Lest'), ('female', 'Default for Frey')]:
            index = record['defaults'][gender][field]
            name = names[index] if index < len(names) else ''
            text = self.ui.text(caption) + f' · #{index}'
            if name: text += ' · ' + name.replace('＠しゅじんこうくん＠', self.ui.text('[Player name]'))
            choices.append((text, index))
        defaults = {index for _text, index in choices}
        for index, name in enumerate(names[:self.constants['nicknameCount']]):
            if name and index not in defaults:
                choices.append((f'#{index} · ' + name.replace('＠しゅじんこうくん＠', self.ui.text('[Player name]')), index))
        stored = record[field]
        if stored not in {index for _text, index in choices}:
            choices.append((self.ui.text(f'Stored nickname ID {stored} · keep unless verified'), stored))
        return choices

    def apply_record(self, key, changes):
        selected = self.selections[key]
        if key == 'skills': self.backend.call('setSkill', id=selected, changes=changes)
        elif key == 'friendship': self.backend.call('setFriendship', id=selected, level=changes['level'])
        elif key == 'relationships': self.backend.call('setRelationship', id=selected, changes=changes)
        elif key == 'people': self.backend.call('setStats', kind='person', id=selected, changes=changes)
        elif key == 'monsters':
            values = {'stats': {field: value for field, value in changes.items() if field != 'friendship'}}
            if 'friendship' in changes: values['friendship'] = changes['friendship']
            self.backend.call('setMonster', id=selected, changes=values)
        elif key == 'trophies': self.backend.call('setTrophy', name=selected, value=changes['value'])
        else:
            record = next(record for record in self.backend.call('recipes') if f'{record["kind"]}:{record["index"]}' == selected)
            self.backend.call('setRecipes', recipes=[record], known=bool(changes['known']))

    def bulk_recipes(self, known, *, all_recipes=False):
        state = self.backend.state()
        if not state or state['kind'] != 'slot': raise ValueError('Open a slot save first.')
        source = self.backend.call('recipes') if all_recipes else self.filtered_recipes()
        records = list({record['bitOffset']: record for record in source}.values())
        if not records: raise ValueError('Read recipe tables first.' if all_recipes else 'No recipes match the current filters.')
        form = self.record_forms['recipes']
        callbacks = [lambda: form.apply_callback(form.changes())] if form.drafts else []
        callbacks.append(lambda: self.backend.call('setRecipes', recipes=records, known=known))
        self.backend.apply_callbacks(callbacks)
        form.drafts.clear(); form.status.setText(self.ui.text('No draft'))
        self.refresh()
        if all_recipes and known:
            self.statusBar().showMessage(self.ui.text('All loaded recipes learned in memory. Export to save.'), 10000)

    def make_marriage(self):
        layout = self.page('marriage', 'Marriage flags', 'Flags only—not a complete marry/divorce operation. Wedding events, pregnancy, children, schedules and system unlocks are not simulated. Back up and test the exported copy.')
        self.marriage_summary = QLabel(); layout.addWidget(self.marriage_summary)
        self.candidate_combo = QComboBox()
        self.candidate_combo.setProperty('gameNames', True)
        layout.addWidget(QLabel('Event candidate (does not change spouse)')); layout.addWidget(self.candidate_combo)
        self.candidate_combo.currentIndexChanged.connect(self.change_candidate)
        fields = [{**field, 'kind': 'choice' if field['key'] in {'spouse', 'season'} else 'bool' if field['max'] == 1 else 'number'} for field in self.constants['marriage']]
        fields += [{'key': 'marriageEvent', 'label': 'Candidate marriage event cleared', 'kind': 'bool'}, {'key': 'newlywedEvent', 'label': 'Candidate newlywed event cleared', 'kind': 'bool'}]
        self.marriage_form = self.form(layout, fields, lambda changes: self.backend.call('setMarriage', candidate=self.candidate, changes=changes))
        self.renderers['marriage'] = self.render_marriage

    def change_candidate(self):
        selected = self.candidate_combo.currentData()
        if selected is None or selected == self.candidate: return
        if self.marriage_form.drafts:
            try: self.apply_form(self.marriage_form, self.marriage_form.apply_callback)
            except ValueError as error:
                with QSignalBlocker(self.candidate_combo): self.candidate_combo.setCurrentIndex(self.candidate_combo.findData(self.candidate))
                self.statusBar().showMessage(self.ui.text(str(error))); return
        self.candidate = selected
        self.render_marriage()

    def render_marriage(self):
        state = self.backend.state(); ready = bool(state and state['kind'] == 'slot'); self.marriage_form.set_ready(ready)
        candidates = self.icon_choices([(self.person_name(person['id']), person['id']) for person in self.constants['candidates']], 'people')
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
        self.flag_group = QComboBox(); combo_options(self.flag_group, [('All flags', 'all')], 'all'); layout.addWidget(self.flag_group)
        self.flag_group.currentIndexChanged.connect(self.render_flags)
        self.flag_search = QLineEdit(); self.flag_search.setPlaceholderText('Find flags / registers by developer name or description'); layout.addWidget(self.flag_search)
        self.flag_selector = QComboBox(); layout.addWidget(self.flag_selector)
        self.flag_search.textChanged.connect(self.render_flags)
        self.flag_selector.currentIndexChanged.connect(lambda: self.change_flag())
        self.flag_info = QLabel(); self.flag_info.setWordWrap(True); self.flag_info.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred); layout.addWidget(self.flag_info)
        self.flag_form = self.form(layout, [{'key': 'value', 'label': 'Value (1-bit flags: 0 or 1)'}], lambda changes: self.backend.call('setFlag', name=self.selections['flags'], value=changes['value']))
        self.flag_impact = QPlainTextEdit(); self.flag_impact.setReadOnly(True); self.flag_impact.setMaximumHeight(170); layout.addWidget(self.flag_impact)
        self.flag_form.draftChanged.connect(self.render_flag_impact)
        row = ResponsiveRow()
        for label, callback in [('Read symbols', self.read_symbols), ('Download progress profile', self.save_profile), ('Read and apply profile', self.read_profile)]:
            button = QPushButton(label); button.clicked.connect(callback); row.addWidget(button)
        layout.addWidget(row)
        self.renderers['flags'] = self.render_flags

    def change_flag(self):
        selected = self.flag_selector.currentData()
        if selected == self.selections['flags']: return
        if self.flag_form.drafts:
            try: self.apply_form(self.flag_form, self.flag_form.apply_callback)
            except ValueError as error:
                with QSignalBlocker(self.flag_selector): self.flag_selector.setCurrentIndex(self.flag_selector.findData(self.selections['flags']))
                self.statusBar().showMessage(self.ui.text(str(error))); return
        self.selections['flags'] = selected
        self.render_flags()

    def render_flags(self):
        state = self.backend.state(); ready = bool(state and state['kind'] == 'slot'); self.flag_form.set_ready(ready)
        if not ready: return
        records = self.backend.call('flags')
        group = self.flag_group.currentData() or 'all'
        combo_options(self.flag_group, [('All flags', 'all')] + [(label, label) for label in sorted({record['group'] for record in records})], group)
        query = self.flag_search.text().strip().casefold()
        matching = [record for record in records if (group == 'all' or record['group'] == group) and (not query or query in f'{record["name"]} {record.get("label", "")} {record.get("description", "")} {record["help"]["title"]["en"]} {record["help"]["title"]["zh"]}'.casefold())]
        selected = self.selections['flags']
        if not self.flag_form.drafts and selected not in {record['name'] for record in matching}:
            selected = matching[0]['name'] if matching else None; self.selections['flags'] = selected
        language = 'zh' if self.ui.code == 'zh-CN' else 'en'
        combo_options(self.flag_selector, [(record['help']['title'][language] + ' · ' + record['name'], record['name']) for record in matching], selected)
        record = next((record for record in records if record['name'] == selected), None)
        self.flag_form.set_ready(bool(record))
        if record:
            help = record['help']
            translation = 'Curated translation; not gameplay validation.' if help['translation'] == 'curated' else 'Symbol interpretation only; meaning unverified.' if help['translation'] == 'symbol interpretation' else 'Unknown meaning — keep the original developer symbol.'
            self.flag_info.setText(f'Bit {record["bitOffset"]} · {record["width"]} bits · range 0–{2 ** record["width"] - 1}\n{help["title"][language]}\n' + self.ui.text('Original developer description') + ': ' + help['original'] + '\n' + self.ui.text(translation) + '\n' + self.ui.text(help['evidence']) + '\n' + help['impact'][language])
            self.flag_form.set_data({'value': record['value']})
        else:
            self.flag_info.clear()
        self.render_flag_impact()
        self.ui.apply(self.pages['flags'][0])

    def render_flag_impact(self):
        if not hasattr(self, 'flag_form') or not self.selections['flags']: return
        try:
            value = self.flag_form.value('value')
            if value in (None, ''): self.flag_impact.clear(); return
            result = self.backend.call('flagImpact', name=self.selections['flags'], value=value)
            language = 'zh' if self.ui.code == 'zh-CN' else 'en'
            lines = [self.ui.text('Evidence / edit impact'), f'{result["name"]}: {result["from"]} → {result["to"]}', result['help']['impact'][language]]
            if result['rewind']: lines.append(self.ui.text('WARNING: story rewind bypasses the game advance-only guard.'))
            if result['stageWitness']:
                lines.append(self.ui.text('Script witness (not a playable preset)') + ': ' + result['stageWitness'][language])
            for before, after in zip(result['beforeConditions'], result['afterConditions']):
                if result['name'] != 'REG_MAIN_SCENARIO' and before == after: continue
                title = after['zh'] if language == 'zh' else after['name']
                passed = self.ui.text('Pass') if after['progressPass'] else self.ui.text('Fail')
                completed = self.ui.text('Pass') if after['completionPass'] else self.ui.text('Fail')
                lines.append(f'{title}: ' + self.ui.text('Progress gate') + f' ≥{after["minimum"]}: {passed}; ' + self.ui.text('Not-completed gate') + f': {completed}; ' + self.ui.text('Overall eligibility') + ': ' + self.ui.text(after['eligibility']))
                lines.append(self.ui.text('Participant-enable queries unresolved; not assumed to be friendship checks.') + ' ' + ', '.join(self.person_name(npc) for npc in after['participants']))
            lines += [f'0x{change["offset"]:05X}: {change["before"]:02X} → {change["after"]:02X}' for change in result['changes']]
            lines.append(self.ui.text('Preview only — no save bytes or undo history are changed.'))
            self.flag_impact.setPlainText('\n'.join(lines))
        except ValueError as error:
            self.flag_impact.setPlainText(self.ui.text('Preview unavailable') + ': ' + self.ui.text(str(error)))

    def read_symbols(self):
        if self.pending(): self.statusBar().showMessage('Apply or clear drafts before replacing symbols.'); return
        filename, _ = QFileDialog.getOpenFileName(self, self.ui.text('Read emdeb.bin'), '', 'Developer symbols (*.bin)')
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
        filename, _ = QFileDialog.getOpenFileName(self, self.ui.text('Read progress profile'), '', 'Progress profile (*.json)')
        if not filename: return
        def load():
            path = Path(filename)
            if path.stat().st_size > 1024 * 1024: raise ValueError('Progress profile is too large.')
            text = path.read_text(encoding='utf-8')
            data = json.loads(text)
            count = len(data.get('flags', {}))
            if self.question('Apply progression flags?', f'Apply {count} named flags as one undoable edit? Events and world state will not be simulated.', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel) == QMessageBox.StandardButton.Yes:
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
        layout = self.page('review', 'Review & export', 'Export writes to the game save folder and creates a backup there first. Save as is available for copies and other platforms.')
        self.review_text = QPlainTextEdit(); self.review_text.setReadOnly(True); layout.addWidget(self.review_text, 1)
        options = QFormLayout()
        options.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.target_save_combo = QComboBox()
        combo_options(self.target_save_combo, [('Choose target save slot', None)] + [(f'rf4_s{slot:02d}.sav', f'rf4_s{slot:02d}.sav') for slot in range(40)] + [('rf4_sys.sav', 'rf4_sys.sav')])
        options.addRow('Target save file', self.target_save_combo)
        self.export_platform = QComboBox(); combo_options(self.export_platform, [('Keep source format', 'keep'), ('PC (experimental if converting)', 'pc'), ('Switch (experimental if converting)', 'switch')], 'keep'); options.addRow('Output platform', self.export_platform)
        self.conversion_consent = QCheckBox(); self.conversion_consent.setChecked(True)
        self.repair_consent = QCheckBox(); self.repair_consent.setChecked(True)
        self.export_gender = QComboBox(); combo_options(self.export_gender, [('Keep edited gender', 'keep'), ('Match original gender', 'original'), ('Male · Lest', 'male'), ('Female · Frey', 'female')], 'keep'); options.addRow('Gender on export', self.export_gender)
        self.reset_appearance, row = wrapping_checkbox('Also reset appearance, portrait and outfit'); options.addRow(row)
        self.reset_dating, row = wrapping_checkbox('Clear incompatible dating and their special nicknames (keep friendship)'); options.addRow(row)
        self.reset_dating.setToolTip('Optional: Lest clears the six bachelors; Frey clears the six bachelorettes. Both forms of address reset. Story/events, date history and other NPCs stay unchanged. Does not repair marriage.')
        self.dating_preview = QLabel(); self.dating_preview.setWordWrap(True); self.dating_preview.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred); options.addRow(self.dating_preview)
        self.export_gender.currentIndexChanged.connect(lambda: self.renderers['review']())
        self.reset_dating.toggled.connect(lambda: self.renderers['review']())
        layout.addLayout(options)
        row = ResponsiveRow()
        for label, callback in [('Save as…', self.save_as), ('Download change report', self.report_file), ('Restore original in memory', lambda: self.mutate('reset')), ('Export edited save', self.export_file)]:
            button = QPushButton(label); button.clicked.connect(callback); row.addWidget(button)
        layout.addWidget(row)
        def render():
            state = self.backend.state()
            if not state:
                self.review_text.setPlainText('Open a save first.'); return
            changes = self.backend.call('changes')
            lines = [f'{state["name"]} · {state["changedBytes"]:,} changed bytes · {state["undo"]} undoable edits', self.ui.text('Pending edits are applied automatically when exporting.')]
            lines += [f'0x{entry["offset"]:05X}: {bytes(entry["before"][:24]).hex(" ")} → {bytes(entry["after"][:24]).hex(" ")}' for entry in changes[:100]]
            if len(changes) > 100: lines.append(f'First 100 of {len(changes)} ranges shown; the JSON report includes all.')
            self.review_text.setPlainText('\n'.join(lines))
            slot = state['kind'] == 'slot'
            self.export_platform.setEnabled(slot); self.export_gender.setEnabled(slot); self.reset_appearance.setEnabled(slot); self.conversion_consent.setEnabled(slot)
            self.reset_dating.setEnabled(slot)
            self.dating_preview.setText('')
            if slot and self.reset_dating.isChecked():
                try:
                    mode = self.export_gender.currentData()
                    if mode == 'keep': raise ValueError('Choose Male, Female or Match original gender for dating cleanup.')
                    gender = mode
                    if mode == 'original':
                        code = self.backend.call('original')[0x36]
                        if code not in (0, 1): raise ValueError('Original gender is unrecognized. Choose Male or Female explicitly.')
                        gender = 'male' if code == 0 else 'female'
                    people = self.backend.call('datingCleanup', gender=gender)
                    self.dating_preview.setText('Will clear dating / reset addresses: ' + ', '.join(person['name'] for person in people) + '. Friendship and event history stay unchanged.')
                except ValueError as error:
                    self.dating_preview.setText(str(error))
        self.renderers['review'] = render

    def export_options(self):
        state = self.backend.state()
        if not state: raise ValueError('Open a save first.')
        slot = state['kind'] == 'slot'
        target = self.export_platform.currentData()
        gender = self.export_gender.currentData() if slot else 'keep'
        return {'platform': state['platform'] if not slot or target == 'keep' else target, 'experimental': True, 'repair': True, 'gender': gender, 'resetAppearance': slot and self.reset_appearance.isChecked(), 'resetDating': slot and self.reset_dating.isChecked()}

    def export_bytes(self):
        if self.demo_mode: raise ValueError('Open a real save first. Synthetic demo export is disabled.')
        self.apply_all_drafts()
        return self.backend.build(**self.export_options())

    def write_file(self, path, data):
        atomic_write(path, data)

    def write_dialog(self, data, suggested, filter):
        filename, _ = QFileDialog.getSaveFileName(self, self.ui.text('Save a new file — keep your backup'), suggested, filter)
        if filename:
            self.write_file(filename, data)
            return True
        return False

    def export_file(self):
        def export():
            data = self.export_bytes()
            state = self.backend.state()
            if state['kind'] == 'slot' and self.export_options()['platform'] != 'pc': raise ValueError('Use PC output for the PC save folder, or choose Save as for Switch.')
            if (state['kind'] == 'system') != (self.target_save_combo.currentData() == 'rf4_sys.sav'): raise ValueError('Choose a target filename matching the save type.')
            target, backup = export_to_game_folder(self.target_save_combo.currentData(), data, bytes(self.backend.call('original')))
            self.source_path = target
            self.backend.call('markExported')
            self.update_export()
            self.statusBar().showMessage(self.ui.text('Saved: ') + str(target) + self.ui.text(' · Backup: ') + str(backup), 15000)
        self.attempt(export)

    def save_as(self):
        def export():
            data = self.export_bytes()
            filename = self.target_save_combo.currentData() or Path(self.backend.state()['name']).stem + '.edited.sav'
            if self.write_dialog(data, str(game_save_directory() / filename), 'RF4S save (*.sav)'):
                self.backend.call('markExported')
                self.update_export()
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
