"""Real Qt shaping checks for bundled English/Chinese Medium faces."""
import ctypes
import importlib.util
import os
from pathlib import Path
import unittest

from scripts.build_desktop import FONT_ASSETS
from scripts.native_bundle_policy import needed

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = importlib.util.find_spec('PySide6') is not None


class FontPackagingTests(unittest.TestCase):
    def test_portable_font_manifest_contains_both_faces_and_licenses(self):
        self.assertIn('NotoSans.ttf', FONT_ASSETS)
        self.assertIn('NotoSansCJKsc-Medium.otf', FONT_ASSETS)
        for filename in FONT_ASSETS:
            path = ROOT / 'web' / 'assets' / 'fonts' / filename
            self.assertTrue(path.is_file(), filename)
            self.assertGreater(path.stat().st_size, 0)
            self.assertTrue(needed((f'web/assets/fonts/{filename}', str(path), 'DATA')))


@unittest.skipUnless(AVAILABLE, 'Native Qt build dependencies are not installed')
class NativeFontTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name == 'nt': ctypes.WinDLL(str(Path(os.environ['SystemRoot']) / 'System32' / 'icuuc.dll'))
        else: os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_interface_uses_medium_weight_and_bundled_family_order(self):
        from PySide6.QtGui import QFont
        from native_fonts import interface_font, FONT_FAMILIES
        for _ in range(2):
            font = interface_font()
            self.assertEqual(font.families(), list(FONT_FAMILIES))
            self.assertEqual(font.weight(), QFont.Weight.Medium)
            self.assertEqual(font.pointSize(), 11)

    def test_mixed_text_shapes_in_both_matching_faces_without_missing_glyphs(self):
        from PySide6.QtGui import QTextLayout
        from native_fonts import interface_font, FONT_FAMILIES
        layout = QTextLayout('English 中文 剧情编辑 繁體字 0123456789', interface_font())
        layout.beginLayout(); line = layout.createLine(); line.setLineWidth(1000); layout.endLayout()
        runs = layout.glyphRuns()
        self.assertEqual({run.rawFont().familyName() for run in runs}, set(FONT_FAMILIES))
        for run in runs:
            self.assertEqual(run.rawFont().weight(), 500)
            self.assertNotIn(0, run.glyphIndexes())

    def test_chinese_font_covers_every_chinese_interface_character(self):
        from PySide6.QtGui import QRawFont
        from native_fonts import FONT_DIRECTORY
        from native_i18n import ZH
        raw = QRawFont(str(FONT_DIRECTORY / 'NotoSansCJKsc-Medium.otf'), 16)
        self.assertTrue(raw.isValid())
        characters = {character for caption in ZH.values() for character in caption if '\u3400' <= character <= '\u9fff'}
        self.assertTrue(characters)
        self.assertEqual([hex(ord(character)) for character in sorted(characters) if not raw.supportsCharacter(ord(character))], [])


if __name__ == '__main__': unittest.main()
