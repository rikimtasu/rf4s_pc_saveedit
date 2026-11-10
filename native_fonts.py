"""Bundled Medium-weight Noto fonts shared with the offline browser interface."""
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase

FONT_DIRECTORY = Path(__file__).resolve().parent / 'web' / 'assets' / 'fonts'
FONT_FAMILIES = ('Noto Sans', 'Noto Sans CJK SC')
_registered = False


def interface_font(point_size=11):
    """Register once; use matching Latin/CJK faces without installing system fonts."""
    global _registered
    if not _registered:
        for filename, family in zip(('NotoSans.ttf', 'NotoSansCJKsc-Medium.otf'), FONT_FAMILIES):
            font_id = QFontDatabase.addApplicationFont(str(FONT_DIRECTORY / filename))
            if font_id < 0 or family not in QFontDatabase.applicationFontFamilies(font_id):
                raise ValueError(f'Cannot load bundled interface font: {filename}')
        _registered = True
    font = QFont()
    font.setFamilies(list(FONT_FAMILIES))
    font.setPointSize(max(10, point_size))
    font.setWeight(QFont.Weight.Medium)
    return font
