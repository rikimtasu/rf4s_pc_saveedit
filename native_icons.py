"""Small raster icons; no browser, image service or game installation needed."""
from pathlib import Path
from zipfile import ZipFile

from PySide6.QtGui import QIcon, QPixmap


class GameIcons:
    def __init__(self, folder=None):
        folder = Path(folder) if folder is not None else Path(__file__).resolve().parent / 'builtin'
        path = folder / 'icons.zip'
        self.archive = ZipFile(path) if path.is_file() else None
        self.index = {}
        self.cache = {}

    def load_index(self, index):
        self.index = index or {}

    def icon(self, kind, identifier):
        name = self.index.get(kind, {}).get(str(identifier))
        if not name or self.archive is None: return QIcon()
        if name not in self.cache:
            pixels = QPixmap()
            try: pixels.loadFromData(self.archive.read(name), 'PNG')
            except KeyError: pass
            self.cache[name] = QIcon(pixels)
        return self.cache[name]
