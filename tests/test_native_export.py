import importlib.util
import ctypes
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

AVAILABLE = importlib.util.find_spec('PySide6') is not None


@unittest.skipUnless(AVAILABLE, 'Native dependencies are not installed')
class NativeExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name == 'nt': ctypes.WinDLL(str(Path(os.environ['SystemRoot']) / 'System32' / 'icuuc.dll'))
    def test_export_backs_up_current_destination_not_stale_loaded_bytes(self):
        from native_export import export_to_game_folder
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'rf4_s01.sav'; target.write_bytes(b'newer game save')
            output, backup = export_to_game_folder('rf4_s01.sav', b'edited', b'old loaded bytes', temp)
            self.assertEqual(output.read_bytes(), b'edited')
            self.assertEqual(backup.read_bytes(), b'newer game save')
            self.assertEqual(backup.parent, output.parent)
            _, second = export_to_game_folder('rf4_s01.sav', b'edited again', b'old loaded bytes', temp)
            self.assertNotEqual(second, backup)
            self.assertEqual(second.read_bytes(), b'edited')
            self.assertEqual(backup.read_bytes(), b'newer game save')

    def test_new_target_keeps_an_original_backup_and_uses_appdata(self):
        from native_export import export_to_game_folder
        with tempfile.TemporaryDirectory() as temp, patch.dict('os.environ', {'APPDATA': temp}):
            target, backup = export_to_game_folder('rf4_sys.sav', b'edited', b'original')
            self.assertEqual(target.parent, Path(temp) / 'Rune Factory 4 Special')
            self.assertEqual(backup.read_bytes(), b'original')

    def test_failed_save_write_leaves_the_original_and_backup_intact(self):
        from native_export import export_to_game_folder
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'rf4_s01.sav'; target.write_bytes(b'original')
            with patch('native_export.atomic_write', side_effect=OSError('write failed')):
                with self.assertRaises(OSError): export_to_game_folder('rf4_s01.sav', b'edited', b'loaded', temp)
            self.assertEqual(target.read_bytes(), b'original')
            self.assertEqual(next(Path(temp).glob('*.bak')).read_bytes(), b'original')

    def test_unsafe_filename_cannot_escape_the_save_folder(self):
        from native_export import export_to_game_folder
        with tempfile.TemporaryDirectory() as temp:
            for name in ['../rf4_s01.sav', 'test.sav', '', 'rf4_s001.sav']:
                with self.assertRaises(ValueError): export_to_game_folder(name, b'edited', b'old', temp)
            self.assertEqual(list(Path(temp).iterdir()), [])
