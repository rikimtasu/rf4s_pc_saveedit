"""Explicit in-place export with a same-folder backup before the atomic save write."""
from datetime import datetime
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import stat
import struct
import zlib

from PySide6.QtCore import QSaveFile, QIODevice

BACKUP_LIMIT = 10
SAVE_NAME = r'rf4_s\d{2}\.sav|rf4_sys\.sav'


@dataclass(frozen=True)
class SaveWriteResult:
    target: Path
    backup: Path
    data: bytes
    cleanup_errors: tuple = ()

    def __iter__(self):
        # Preserve the existing two-value export interface.
        yield self.target
        yield self.backup


def _filename(filename):
    if not re.fullmatch(SAVE_NAME, filename or '', re.IGNORECASE):
        raise ValueError('Choose a target save slot first.')
    return filename.lower()


def _backup_match(filename, name):
    return re.fullmatch(re.escape(filename) + r'\.backup-(\d{8}-\d{6}-\d{6})-(\d+)\.bak', name, re.IGNORECASE)


def list_backups(filename, directory=None):
    """List only this editor's regular, same-save backups; never follow links."""
    filename = _filename(filename)
    folder = Path(directory) if directory is not None else game_save_directory()
    if not folder.exists(): return []
    records = []
    for path in folder.iterdir():
        match = _backup_match(filename, path.name)
        if not match: continue
        try:
            created = datetime.strptime(match[1], '%Y%m%d-%H%M%S-%f')
            info = path.lstat()
        except (ValueError, FileNotFoundError): continue
        if not stat.S_ISREG(info.st_mode) or path.is_symlink(): continue
        records.append({'name': path.name, 'path': str(path), 'created': created.isoformat(' ', timespec='microseconds'),
                        'size': info.st_size, 'sequence': int(match[2])})
    return sorted(records, key=lambda entry: (entry['created'], entry['sequence']), reverse=True)


def save_info(data):
    """Read-only snapshot details; validity is a container/CRC check, not gameplay."""
    data = bytes(data)
    info = {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'crc_valid': False,
            'kind': 'unknown', 'platform': 'unknown', 'format': 'Unsupported save format'}
    if len(data) == 9304 and data[:4] == b'RF4D':
        info.update(kind='system', platform='shared', format='System save', system_flags=struct.unpack_from('<I', data, 0x10)[0])
        stored = struct.unpack_from('<I', data, 4)[0]; computed = zlib.crc32(data[8:])
    elif len(data) in (140424, 140416):
        platform = 'pc' if len(data) == 140424 else 'switch'
        info.update(kind='slot', platform=platform, format='PC slot' if platform == 'pc' else 'Switch slot',
                    calendar={'day': struct.unpack_from('<I', data, 0x14)[0], 'season': struct.unpack_from('<I', data, 0x18)[0], 'year': struct.unpack_from('<I', data, 0x1c)[0]},
                    gender={0: 'Lest', 1: 'Frey'}.get(data[0x36], 'Unknown'), money=struct.unpack_from('<i', data, 0x4c)[0],
                    order_points=struct.unpack_from('<i', data, 0x20710)[0], tourists=struct.unpack_from('<i', data, 0x20714)[0])
        stored = struct.unpack_from('<I', data)[0]; computed = zlib.crc32(data[4:-224])
    else: return info
    info.update(crc_valid=stored == computed, stored_crc=f'{stored:08X}', computed_crc=f'{computed:08X}')
    return info


def _read_backup(filename, backup_name, directory=None):
    filename = _filename(filename)
    if not _backup_match(filename, backup_name or ''): raise ValueError('Choose a backup belonging to the selected save.')
    folder = Path(directory) if directory is not None else game_save_directory()
    path = folder / backup_name
    if path.is_symlink() or not stat.S_ISREG(path.lstat().st_mode): raise ValueError('Refusing to read a linked or non-file backup.')
    # Bounded read even if a managed-looking file is replaced or grows.
    with path.open('rb') as stream: data = stream.read(140425)
    return path, data


def inspect_backup(filename, backup_name, directory=None):
    path, data = _read_backup(filename, backup_name, directory)
    info = save_info(data)
    size = path.stat().st_size
    if size != len(data): info.update(sha256=None, crc_valid=False)
    info.update(name=path.name, path=str(path), size=size, restorable=info['crc_valid'] and
                (info['kind'] == 'system' if _filename(filename) == 'rf4_sys.sav' else info['kind'] == 'slot' and info['platform'] == 'pc'))
    return info


def _prune_backups(filename, folder, newest):
    records = list_backups(filename, folder)
    keep = {newest.name}
    for record in records:
        if len(keep) >= BACKUP_LIMIT: break
        keep.add(record['name'])
    errors = []
    for record in records:
        if record['name'] in keep: continue
        path = folder / record['name']
        try:
            if path.is_symlink() or not stat.S_ISREG(path.lstat().st_mode): continue
            path.unlink()
        except FileNotFoundError: continue
        except OSError as error: errors.append(f'{path.name}: {error}')
    return tuple(errors)


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
    filename = _filename(filename)
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
    data = bytes(data)
    atomic_write(target, data)
    # Cleanup cannot undo a successful save or conceal that it reached disk.
    # Never prune before the atomic write succeeds; failed writes retain backups.
    try: errors = _prune_backups(filename, folder, backup)
    except OSError as error: errors = (str(error),)
    return SaveWriteResult(target, backup, data, errors)


def restore_backup(filename, backup_name, expected_sha256, directory=None):
    """Restore a reviewed, valid backup byte-for-byte, preserving current disk bytes."""
    path, data = _read_backup(filename, backup_name, directory)
    info = save_info(data)
    if info['sha256'] != expected_sha256: raise ValueError('The backup changed since the preview. Refresh and review it again.')
    if not info['crc_valid']: raise ValueError('Backup has an invalid checksum or unsupported format. Restore refused.')
    if (info['kind'] == 'system') != (_filename(filename) == 'rf4_sys.sav') or info['platform'] == 'switch':
        raise ValueError('Choose a matching PC slot or system-save backup for direct rollback.')
    return export_to_game_folder(filename, data, data, path.parent)
