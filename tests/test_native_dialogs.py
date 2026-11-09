"""Exercise real modal Qt dialogs, including standard-button translation fallback."""
import ctypes
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = importlib.util.find_spec('PySide6') is not None and (ROOT / 'web/native-bundle.js').is_file()


@unittest.skipUnless(AVAILABLE, 'Native build dependencies / compiled core are not installed')
class NativeDialogTests(unittest.TestCase):
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

    def tearDown(self):
        self.window.closing = True
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def capture(self, invoke):
        from PySide6.QtCore import QTimer, Qt
        from PySide6.QtWidgets import QMessageBox, QLabel
        captured = {}

        def inspect():
            dialog = self.app.activeModalWidget()
            if isinstance(dialog, QMessageBox):
                captured.update(title=dialog.windowTitle(), text=dialog.text(),
                                width=dialog.width(), title_width=dialog.fontMetrics().horizontalAdvance(dialog.windowTitle()),
                                buttons={dialog.standardButton(button): button.text() for button in dialog.buttons()},
                                default=dialog.standardButton(dialog.defaultButton()), clipped=[])
                for label in dialog.findChildren(QLabel):
                    if label.text():
                        needed = label.fontMetrics().boundingRect(label.contentsRect(), int(label.alignment()) | int(Qt.TextFlag.TextWordWrap), label.text())
                        if needed.height() > label.contentsRect().height() or needed.width() > label.contentsRect().width():
                            captured['clipped'].append(label.text())
                dialog.button(QMessageBox.StandardButton.Cancel).click()
            elif dialog:
                dialog.reject()

        QTimer.singleShot(0, inspect)
        result = invoke()
        self.assertTrue(captured, 'The actual QMessageBox did not open')
        return captured, result

    def test_discard_confirmation_has_readable_buttons_and_body_in_both_languages(self):
        from PySide6.QtWidgets import QMessageBox
        for code, captions in [('en', ['Discard', 'Cancel']), ('zh-CN', ['放弃', '取消']), ('en', ['Discard', 'Cancel'])]:
            with self.subTest(language=code):
                self.window.ui_language_combo.setCurrentIndex(self.window.ui_language_combo.findData(code))
                with patch.object(self.window, 'pending', return_value=True):
                    captured, result = self.capture(self.window.discard_confirmation)
                self.assertFalse(result, 'Cancel must keep unexported work')
                self.assertEqual(captured['default'], QMessageBox.StandardButton.Cancel)
                self.assertEqual(captured['text'], self.window.ui.text('Discard unexported edits and drafts?'))
                self.assertEqual(captured['title'], self.window.ui.text('Unexported changes'))
                self.assertGreaterEqual(captured['width'], max(360, captured['title_width'] + 120), 'Dialog title needs room for native window controls')
                self.assertEqual(captured['clipped'], [])
                actual = [captured['buttons'][button].replace('&', '') for button in
                          (QMessageBox.StandardButton.Discard, QMessageBox.StandardButton.Cancel)]
                self.assertEqual(actual, captions, 'Standard confirmation buttons must not be blank')

    def test_unmapped_standard_button_retains_its_english_caption(self):
        from PySide6.QtWidgets import QMessageBox
        for code in ['en', 'zh-CN']:
            with self.subTest(language=code):
                self.window.ui_language_combo.setCurrentIndex(self.window.ui_language_combo.findData(code))
                captured, _ = self.capture(lambda: QMessageBox.question(self.window, 'Retry test', 'Try again?',
                    QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel))
                self.assertEqual(captured['buttons'][QMessageBox.StandardButton.Retry].replace('&', ''), 'Retry')

    def test_progression_confirmation_wraps_larger_text_and_keeps_cancel_default(self):
        from PySide6.QtWidgets import QMessageBox
        font = self.window.font(); font.setPointSize(14); self.window.setFont(font)
        for code in ['en', 'zh-CN']:
            with self.subTest(language=code):
                self.window.ui_language_combo.setCurrentIndex(self.window.ui_language_combo.findData(code))
                captured, result = self.capture(lambda: self.window.question('Apply progression flags?',
                    'Apply 100 named flags as one undoable edit? Events and world state will not be simulated.',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel))
                self.assertEqual(result, QMessageBox.StandardButton.Cancel)
                self.assertEqual(captured['default'], QMessageBox.StandardButton.Cancel)
                self.assertEqual(captured['clipped'], [])
                self.assertTrue(all(text.strip() for text in captured['buttons'].values()))


if __name__ == '__main__': unittest.main()
