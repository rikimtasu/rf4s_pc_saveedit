"""Build the small native Windows executable, without browser/server assets."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--include-local', action='store_true', help='Private build only: include generated game references.')
    parser.add_argument('--game', type=Path, help='Prepare bundled catalog/icons from this game copy before building.')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    if sys.platform != 'win32': parser.error('Build the Windows executable on Windows.')
    if args.game:
        subprocess.run([sys.executable, '-m', 'scripts.generate_builtin', str(args.game)], cwd=ROOT, check=True)
    builtin = ROOT / 'builtin'
    if not (builtin / 'references.json.gz').is_file() or not (builtin / 'icons.zip').is_file():
        parser.error('Prepare the standalone catalog/icons with python -m scripts.generate_builtin <game-folder>, or use --game.')
    subprocess.run([shutil.which('npm.cmd') or 'npm', 'run', 'build:native-core'], cwd=ROOT, check=True)
    temp_base = Path(tempfile.gettempdir()) / 'opencode'
    with tempfile.TemporaryDirectory(prefix='rf4s-native-package-', dir=temp_base if temp_base.is_dir() else None) as temp:
        staging = Path(temp)
        (staging / 'sitecustomize.py').write_text("import ctypes, os\nfrom pathlib import Path\nif os.name == 'nt':\n    ctypes.WinDLL(str(Path(os.environ['SystemRoot']) / 'System32' / 'icuuc.dll'))\n", encoding='utf-8')
        environment = dict(os.environ)
        environment['PYTHONPATH'] = str(staging) + os.pathsep + environment.get('PYTHONPATH', '')
        subprocess.run([sys.executable, '-c', 'from PySide6.QtQml import QJSEngine; from PySide6.QtWidgets import QWidget; print("Native Qt preflight passed")'], env=environment, check=True)
        web = staging / 'web'; web.mkdir()
        shutil.copy2(ROOT / 'web' / 'native-bundle.js', web / 'native-bundle.js')
        for filename, symbol in [('local-game-data.js', 'LOCAL_GAME_DATA'), ('local-save-reference.js', 'LOCAL_SAVE_REFERENCE'), ('local-languages.js', 'LOCAL_LANGUAGES')]:
            source = ROOT / 'web' / filename
            if args.include_local and source.is_file(): shutil.copy2(source, web / filename)
            else: (web / filename).write_text(f'export const {symbol} = null;\n', encoding='utf-8')
        datas = [(str(web), 'web'), (str(ROOT / 'vendor' / 'venti' / 'schema.json'), 'vendor/venti')]
        datas.extend((str(builtin / filename), 'builtin') for filename in ['references.json.gz', 'icons.zip'])
        datas.extend((str(ROOT / filename), '.') for filename in ['COPYING', 'ATTRIBUTION.md'])
        spec = staging / 'RF4S Save Editor.spec'
        # QJSEngine runs binary-save algorithms only, not QML or a browser. Qt's
        # default hook otherwise sweeps every QML plugin and its rendering DLLs.
        spec.write_text(f"""
a = Analysis([{str(ROOT / 'desktop.py')!r}], pathex=[{str(ROOT)!r}, {str(ROOT / 'vendor' / 'rf4-modkit')!r}], binaries=[], datas={datas!r}, hiddenimports=[], excludes=['PyQt5','PyQt6','webview','sitecustomize','PySide6.QtWebEngineCore','PySide6.QtWebEngineWidgets','PySide6.QtWebChannel','PySide6.QtQuick','PySide6.QtQuickWidgets'], noarchive=False)
from scripts.native_bundle_policy import needed
a.datas = [entry for entry in a.datas if needed(entry)]
a.binaries = [entry for entry in a.binaries if needed(entry)]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='RF4S Save Editor', debug=False, strip=False, upx=False, console=False, disable_windowed_traceback=False)
""", encoding='utf-8')
        command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--distpath', str(args.output.resolve()), '--workpath', str(staging / 'build'), str(spec)]
        subprocess.run(command, cwd=ROOT, env=environment, check=True)
    executable = args.output / 'RF4S Save Editor.exe'
    print(f'Native executable: {executable} ({executable.stat().st_size / 1048576:.1f} MiB)')


if __name__ == '__main__':
    main()
