"""Portable native Qt Widgets editor: no browser, Chromium, HTML or local server."""
import argparse
import ctypes
import os
from pathlib import Path
import sys

# Conda Python can shadow Windows' ICU DLL. The portable EXE also works with an
# ordinary Windows PATH and does not require Conda or installed Python.
if os.name == 'nt':
    ctypes.WinDLL(str(Path(os.environ['SystemRoot']) / 'System32' / 'icuuc.dll'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from native_ui import NativeWindow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', type=Path, help='Test native controls using a synthetic save only.')
    parser.add_argument('--self-test-game', type=Path, help='Read game references during the GUI test.')
    args = parser.parse_args()
    app = QApplication(sys.argv)
    app.setApplicationName('RF4S Save Editor')
    app.setApplicationVersion('0.4.0')
    window = NativeWindow()
    if args.self_test:
        from scripts.desktop_smoke import run
        run(app, window, args.self_test, args.self_test_game)
    window.show()
    if not args.self_test:
        # Open the save picker at the RF4S roaming folder, never auto-load a save.
        QTimer.singleShot(0, window.open_file)
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
