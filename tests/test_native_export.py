import importlib.util
import ctypes
import os
from pathlib import Path
import tempfile
import struct
import zlib
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

    def test_only_ten_managed_backups_per_save_are_retained(self):
        from native_export import export_to_game_folder, list_backups
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp); manual = folder / 'rf4_s01.sav.manual.bak'; manual.write_bytes(b'manual')
            other = export_to_game_folder('rf4_s02.sav', b'other', b'other original', temp).backup
            for number in range(14): export_to_game_folder('rf4_s01.sav', str(number).encode(), b'loaded', temp)
            backups = list_backups('rf4_s01.sav', temp)
            self.assertEqual(len(backups), 10)
            self.assertEqual((folder / 'rf4_s01.sav').read_bytes(), b'13')
            self.assertEqual((folder / backups[0]['name']).read_bytes(), b'12')
            self.assertEqual((folder / backups[-1]['name']).read_bytes(), b'3')
            self.assertEqual(manual.read_bytes(), b'manual'); self.assertTrue(other.exists())

    def test_rollback_is_byte_exact_and_backs_up_current_disk_bytes(self):
        from native_export import export_to_game_folder, inspect_backup, restore_backup, list_backups
        first = self.slot(111); second = self.slot(222)
        with tempfile.TemporaryDirectory() as temp:
            result = export_to_game_folder('rf4_s01.sav', second, first, temp)
            info = inspect_backup('rf4_s01.sav', result.backup.name, temp)
            self.assertTrue(info['restorable']); self.assertEqual(info['money'], 111)
            restored = restore_backup('rf4_s01.sav', result.backup.name, info['sha256'], temp)
            self.assertEqual(restored.target.read_bytes(), first); self.assertEqual(restored.data, first)
            self.assertEqual(restored.backup.read_bytes(), second)
            self.assertEqual(len(list_backups('rf4_s01.sav', temp)), 2)

    @staticmethod
    def slot(money):
        data = bytearray(140424)
        struct.pack_into('<III', data, 0x14, 2, 0, 1)
        struct.pack_into('<i', data, 0x4c, money)
        struct.pack_into('<iiHHIII', data, 0x54, 30, 30, 20, 20, 5, 5, 5)
        struct.pack_into('<I', data, 0, zlib.crc32(data[4:-224]))
        return bytes(data)

    def test_changed_damaged_wrong_save_and_path_traversal_backups_are_refused(self):
        from native_export import export_to_game_folder, inspect_backup, restore_backup
        first, second = self.slot(111), self.slot(222)
        with tempfile.TemporaryDirectory() as temp:
            result = export_to_game_folder('rf4_s01.sav', second, first, temp)
            info = inspect_backup('rf4_s01.sav', result.backup.name, temp)
            result.backup.write_bytes(second)
            with self.assertRaises(ValueError): restore_backup('rf4_s01.sav', result.backup.name, info['sha256'], temp)
            for filename, name in [('rf4_s02.sav', result.backup.name), ('rf4_s01.sav', '../' + result.backup.name)]:
                with self.assertRaises(ValueError): inspect_backup(filename, name, temp)
            result.backup.write_bytes(b'corrupt')
            broken = inspect_backup('rf4_s01.sav', result.backup.name, temp)
            self.assertFalse(broken['restorable'])
            with self.assertRaises(ValueError): restore_backup('rf4_s01.sav', result.backup.name, broken['sha256'], temp)
            self.assertEqual(result.target.read_bytes(), second)

    def test_cleanup_failure_does_not_misreport_a_successful_save(self):
        from native_export import export_to_game_folder, list_backups
        with tempfile.TemporaryDirectory() as temp:
            for number in range(10): export_to_game_folder('rf4_s01.sav', str(number).encode(), b'original', temp)
            with patch.object(Path, 'unlink', side_effect=PermissionError('locked backup')):
                result = export_to_game_folder('rf4_s01.sav', b'saved', b'original', temp)
            self.assertEqual(result.target.read_bytes(), b'saved'); self.assertTrue(result.cleanup_errors)
            self.assertEqual(len(list_backups('rf4_s01.sav', temp)), 11)

    def test_invalid_system_signature_and_switch_backup_cannot_restore_to_pc_folder(self):
        from native_export import export_to_game_folder, inspect_backup, restore_backup
        with tempfile.TemporaryDirectory() as temp:
            data = bytearray(140416); struct.pack_into('<I', data, 0, zlib.crc32(data[4:-224]))
            result = export_to_game_folder('rf4_s01.sav', self.slot(222), data, temp)
            info = inspect_backup('rf4_s01.sav', result.backup.name, temp)
            self.assertFalse(info['restorable'])
            with self.assertRaises(ValueError): restore_backup('rf4_s01.sav', result.backup.name, info['sha256'], temp)

    def test_system_backup_info_and_restore_preserve_all_system_bytes(self):
        from native_export import export_to_game_folder, inspect_backup, restore_backup
        first = bytearray(9304); first[:4] = b'RF4D'
        struct.pack_into('<I', first, 0x10, 33); struct.pack_into('<I', first, 4, zlib.crc32(first[8:]))
        second = bytearray(first); struct.pack_into('<I', second, 0x10, 1); struct.pack_into('<I', second, 4, zlib.crc32(second[8:]))
        with tempfile.TemporaryDirectory() as temp:
            result = export_to_game_folder('rf4_sys.sav', second, first, temp)
            info = inspect_backup('rf4_sys.sav', result.backup.name, temp)
            self.assertTrue(info['restorable']); self.assertEqual(info['system_flags'], 33)
            restored = restore_backup('rf4_sys.sav', result.backup.name, info['sha256'], temp)
            self.assertEqual(restored.target.read_bytes(), bytes(first)); self.assertEqual(restored.backup.read_bytes(), bytes(second))
