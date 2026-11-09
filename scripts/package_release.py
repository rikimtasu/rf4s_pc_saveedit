"""Package a public native release; reject personal reference data or browser assets."""
import argparse
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile, ZIP_DEFLATED

from PyInstaller.archive.readers import CArchiveReader

ROOT = Path(__file__).resolve().parents[1]
LICENSES = {
    'Qt-LGPL-3.0.txt': 'https://raw.githubusercontent.com/qt/qtbase/v6.10.2/LICENSES/LGPL-3.0-only.txt',
    'Python-3.10.18.txt': 'https://raw.githubusercontent.com/python/cpython/v3.10.18/LICENSE',
    'OpenSSL-3.6.2.txt': 'https://raw.githubusercontent.com/openssl/openssl/openssl-3.6.2/LICENSE.txt',
}


def validate_public(executable):
    archive = CArchiveReader(str(executable))
    names = {name.replace('\\', '/'): name for name in archive.toc}
    for filename, symbol in [('local-game-data.js', 'LOCAL_GAME_DATA'), ('local-save-reference.js', 'LOCAL_SAVE_REFERENCE'), ('local-languages.js', 'LOCAL_LANGUAGES')]:
        raw = archive.extract(names[f'web/{filename}'])
        if raw.decode('utf-8').strip() != f'export const {symbol} = null;':
            raise ValueError('Refusing to publish a private build containing personal game references.')
    forbidden = [name for name in names if any(token in name.lower() for token in ['webengine', 'chromium', 'qt6quick']) or name.lower().endswith(('.sav', '.html', '.css'))]
    if forbidden:
        raise ValueError(f'Unexpected public release assets: {forbidden}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('--version', default='v0.2')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.output: args.output = ROOT / 'dist' / f'RF4S-Save-Editor-{args.version}-win-x64.zip'
    validate_public(args.executable)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    notices = {}
    for filename, url in LICENSES.items():
        with urlopen(url, timeout=30) as response:
            data = response.read(1024 * 1024 + 1)
        if len(data) > 1024 * 1024 or b'<html' in data.lower() or len(data) < 100:
            raise ValueError(f'Unexpected license response: {filename}')
        notices[filename] = data
    folder = f'RF4S-Save-Editor-{args.version}'
    with ZipFile(args.output, 'w', compression=ZIP_DEFLATED, compresslevel=9) as package:
        package.write(args.executable, f'{folder}/RF4S Save Editor.exe')
        package.writestr(f'{folder}/README.md', f'''# RF4S Save Editor {args.version}

Extract this folder and open **RF4S Save Editor.exe**. Windows 10/11 x64;
no installation, Python, Node or browser is needed.

Back up the entire save folder and close the game before editing. Saves are
not uploaded or automatically overwritten; enable editing, Apply, then export.
Use **Read game folder** to load your own item/recipe/name references.

For player-name editing, open **rf4_sys.sav** and select the matching bank/slot.
For dating and nickname editing, open an individual slot save.

If an older build edited Barrett/Raven friendship or system flags, reapply
those edits from a pre-edit backup; unrelated old changes are not guessed away.

See [native usage](docs/native-desktop.md), [name/relationship guidance](docs/player-name-and-relationships.md)
and [release notes](RELEASE_NOTES.md). Source: https://github.com/rikimtasu/rf4s_pc_saveedit
''')
        package.write(ROOT / 'RELEASE_NOTES.md', f'{folder}/RELEASE_NOTES.md')
        for document in sorted((ROOT / 'docs').glob('*.md')):
            package.write(document, f'{folder}/docs/{document.name}')
        package.write(ROOT / 'ATTRIBUTION.md', f'{folder}/ATTRIBUTION.md')
        package.write(ROOT / 'COPYING', f'{folder}/licenses/Editor-GPL-3.0.txt')
        package.write(ROOT / 'vendor' / 'rf4-modkit' / 'LICENSE', f'{folder}/licenses/rf4-modkit-MIT.txt')
        for filename, data in notices.items():
            package.writestr(f'{folder}/licenses/{filename}', data)
    print(f'Public {args.version} package: {args.output} ({args.output.stat().st_size / 1048576:.1f} MiB)')


if __name__ == '__main__':
    main()
