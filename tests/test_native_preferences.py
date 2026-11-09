import ctypes
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

AVAILABLE = importlib.util.find_spec('PySide6') is not None


@unittest.skipUnless(AVAILABLE, 'Native build dependencies are not installed')
class NativePreferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name == 'nt': ctypes.WinDLL(str(Path(os.environ['SystemRoot']) / 'System32' / 'icuuc.dll'))
        from native_ui import default_save_directory, system_ui_language
        cls.folder = staticmethod(default_save_directory)
        cls.language = staticmethod(system_ui_language)

    def test_system_language_detects_all_chinese_locales_and_english_fallback(self):
        for name in ['zh_CN', 'zh_TW', 'zh_HK', 'zh_Hans_CN', 'zh_Hant_TW']:
            self.assertEqual(self.language(name), 'zh-CN')
        for name in ['en_US', 'ja_JP', 'de_DE', 'ko_KR']:
            self.assertEqual(self.language(name), 'en')

    def test_appdata_game_folder_and_safe_fallback(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {'APPDATA': temp}):
            self.assertEqual(self.folder(), Path.home())
            folder = Path(temp) / 'Rune Factory 4 Special'; folder.mkdir()
            self.assertEqual(self.folder(), folder)


if __name__ == '__main__': unittest.main()
