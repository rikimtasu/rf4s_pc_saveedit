"""Explicit in-place export with a same-folder backup before the atomic save write."""
from datetime import datetime
import os
from pathlib import Path
import re

from PySide6.QtCore import QSaveFile, QIODevice


def game_save_directory():
    appdata = os.environ.get('APPDATA')
    return Path(appdata) / 'Rune Factory 4 Special' if appdata else Path.home() / 'AppData' / 'Roaming' / 'Rune Factory 4 Special'


def atomic_write(path, data):
    file = QSaveFile(str(path))
    file.setDirectWriteFallback(False)
    if not file.open(QIODevice.OpenModeFlag.WriteOnly): raise OSError(file.errorString())
    if file.write(data) != len(data) or not file.commit():
        file.cancelWriting()
        raise OSError(file.errorString())


def export_to_game_folder(filename, data, original, directory=None):
    if not re.fullmatch(r'rf4_s\d{2}\.sav|rf4_sys\.sav', filename or '', re.IGNORECASE):
        raise ValueError('Choose a target save slot first.')
    folder = Path(directory) if directory is not None else game_save_directory()
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / filename.lower()
    if target.is_symlink(): raise ValueError('Refusing to overwrite a linked save file.')
    previous = target.read_bytes() if target.exists() else bytes(original)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    for suffix in range(100):
        backup = folder / f'{target.name}.backup-{stamp}-{suffix}.bak'
        try:
            with backup.open('xb') as stream:
                if stream.write(previous) != len(previous): raise OSError('Incomplete backup write.')
                stream.flush(); os.fsync(stream.fileno())
            break
        except FileExistsError: continue
    else: raise OSError('Could not create a unique backup filename.')
    atomic_write(target, bytes(data))
    return target, backup
