"""Focused native checks: named controls and safe backup rollback; no EXE smoke."""
import ctypes
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

AVAILABLE = importlib.util.find_spec('PySide6') is not None


@unittest.skipUnless(AVAILABLE, 'Native dependencies are not installed')
class BackupsAndOrderNamesUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name == 'nt': ctypes.WinDLL(str(Path(os.environ['SystemRoot']) / 'System32' / 'icuuc.dll'))
        else: os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from native_ui import NativeWindow
        with patch('native_ui.QSettings') as settings:
            settings.return_value.value.return_value = 'en'
            self.window = NativeWindow()
        self.window.testing = True; self.window.test_errors = []
        self.original = bytes(self.window.backend.call('demoBytes'))
        self.window.open_bytes(self.original, 'rf4_s01.sav')

    def tearDown(self):
        self.window.closing = True; self.window.close(); self.window.deleteLater(); self.app.processEvents()

    def test_bgm_names_and_independent_npc_caller_preserve_bytes_until_apply(self):
        self.window.navigation.setCurrentRow(self.window.pages['orders'][2])
        form = self.window.orders_forms['other']
        bgm = form.controls['bgm']; caller = form.controls['morningCaller']
        self.assertEqual(bgm.itemText(bgm.findData(0)), 'Rune Factory 4')
        self.assertIn('Frontier', bgm.itemText(bgm.findData(4)))
        self.assertEqual(caller.itemText(caller.findData(1)), 'Vishnal')
        self.assertEqual(caller.itemText(caller.findData(309)), 'Pico')
        for key, value in [('bgm', 5), ('morningCaller', 309)]: form.write(key, value); form.track(key)
        self.assertEqual(bytes(self.window.backend.call('working')), self.original)
        self.window.apply_all_drafts()
        values = self.window.backend.call('orders')
        self.assertEqual(values['bgm'], 5); self.assertEqual(values['morningCaller'], 309)
        self.assertEqual(values['morningCallOrder'], 0)
        self.window.mutate('undo'); self.assertEqual(bytes(self.window.backend.call('working')), self.original)

    def test_rollback_cancel_keeps_drafts_and_confirm_restores_disk_and_editor(self):
        from native_export import export_to_game_folder
        from PySide6.QtWidgets import QMessageBox
        with tempfile.TemporaryDirectory() as temp, patch.dict('os.environ', {'APPDATA': temp}):
            self.window.backend.call('setPlayer', changes={'money': 222})
            current = self.window.backend.build()
            folder = Path(temp) / 'Rune Factory 4 Special'
            export_to_game_folder('rf4_s01.sav', current, self.original, folder)
            self.window.navigation.setCurrentRow(self.window.pages['backups'][2])
            self.window.render_backups()
            self.assertIn('Checksum: Valid', self.window.backup_preview.toPlainText())
            self.assertIn('Money: 200', self.window.backup_preview.toPlainText())
            self.window.player_form.write('money', 999); self.window.player_form.track('money')
            with patch.object(self.window, 'question', return_value=QMessageBox.StandardButton.No): self.window.restore_selected_backup()
            self.assertTrue(self.window.player_form.drafts); self.assertEqual((folder / 'rf4_s01.sav').read_bytes(), current)
            with patch.object(self.window, 'question', return_value=QMessageBox.StandardButton.Yes): self.window.restore_selected_backup()
            self.assertEqual((folder / 'rf4_s01.sav').read_bytes(), self.original)
            self.assertEqual(bytes(self.window.backend.call('working')), self.original)
            self.assertFalse(self.window.pending()); self.assertEqual(self.window.backend.state()['undo'], 0)
            self.assertTrue(any(path.read_bytes() == current for path in folder.glob('*.bak')))

    def test_rollback_failure_keeps_working_save_and_drafts(self):
        from native_export import export_to_game_folder
        from PySide6.QtWidgets import QMessageBox
        with tempfile.TemporaryDirectory() as temp, patch.dict('os.environ', {'APPDATA': temp}):
            folder = Path(temp) / 'Rune Factory 4 Special'
            export_to_game_folder('rf4_s01.sav', self.original, self.original, folder)
            self.window.navigation.setCurrentRow(self.window.pages['backups'][2]); self.window.render_backups()
            self.window.player_form.write('money', 999); self.window.player_form.track('money')
            with patch.object(self.window, 'question', return_value=QMessageBox.StandardButton.Yes), patch('native_export.atomic_write', side_effect=OSError('write failed')):
                with self.assertRaises(OSError): self.window.restore_selected_backup()
            self.assertEqual(bytes(self.window.backend.call('working')), self.original)
            self.assertTrue(self.window.player_form.drafts)
