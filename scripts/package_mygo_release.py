"""Package the MyGO Windows executable, curated assets and license notices."""
import argparse
import gzip
import io
import json
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
FONT_FILES = {
    'NotoSans.ttf', 'NotoSansCJKsc-Medium.otf',
    'NotoSans-OFL.txt', 'NotoSansCJK-OFL.txt', 'NotoSans-README.md',
}


def validate_public(executable, assets, bundle):
    binary = executable.read_bytes()
    if not binary.startswith(b'MZ'):
        raise ValueError('Expected a Windows executable.')
    if assets.read_bytes() not in binary or bundle.read_bytes() not in binary:
        raise ValueError('Rebuild the executable with the current core and assets before packaging.')
    with ZipFile(assets) as archive:
        expected = {'zh.json', 'references.json.gz', 'icons.zip'} | {'fonts/' + name for name in FONT_FILES}
        if set(archive.namelist()) != expected:
            raise ValueError('Public releases require the curated catalog, icons, fonts and no extra assets.')
        references = json.loads(gzip.decompress(archive.read('references.json.gz')))
        if set(references) != {'items', 'recipes', 'languages', 'icons'}:
            raise ValueError('Unexpected standalone reference payload.')
        with ZipFile(io.BytesIO(archive.read('icons.zip'))) as icons:
            if not icons.namelist() or any(not re.fullmatch(r'[^/\\]+\.png', name) for name in icons.namelist()):
                raise ValueError('Expected only flat PNG icon files.')


def go_notices(executable):
    build_info = subprocess.check_output(['go', 'version', '-m', str(executable)], cwd=ROOT, text=True, encoding='utf-8')
    used = {parts[1] for line in build_info.splitlines() if len(parts := line.split()) >= 3 and parts[0] == 'dep'}
    raw = subprocess.check_output(['go', 'list', '-mod=mod', '-m', '-json', 'all'], cwd=ROOT, text=True, encoding='utf-8')
    decoder = json.JSONDecoder()
    modules = []
    while raw.strip():
        module, end = decoder.raw_decode(raw.lstrip())
        modules.append(module)
        raw = raw.lstrip()[end:]
    notices = {}
    inventory = []
    for module in modules:
        if module['Path'] not in used:
            continue
        directory = Path(module['Dir'])
        files = [path for path in directory.iterdir() if path.is_file() and path.name.upper().startswith(('LICENSE', 'LICENCE', 'COPYING', 'NOTICE', 'AUTHORS', 'PATENTS'))]
        if not files:
            raise ValueError(f'No license notice found for {module["Path"]}.')
        name = module['Path'].replace('/', '_')
        for path in files:
            notices[f'{name}/{path.name}'] = path.read_bytes()
        inventory.append(f'{module["Path"]} {module["Version"]}')
    goroot = Path(subprocess.check_output(['go', 'env', 'GOROOT'], cwd=ROOT, text=True).strip())
    notices['Go-LICENSE.txt'] = (goroot / 'LICENSE').read_bytes()
    notices['Go-modules.txt'] = ('\n'.join(sorted(inventory)) + '\n').encode()
    return notices


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', type=Path, default=ROOT / 'dist' / 'mygo' / 'RF4S Save Editor.exe')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    version = 'v' + json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))['version'].removesuffix('.0')
    if not re.fullmatch(r'v\d+\.\d+(?:\.\d+)?', version):
        raise ValueError('Invalid release version.')
    output = args.output or ROOT / 'dist' / f'RF4S-Save-Editor-{version}-win-x64.zip'
    validate_public(args.executable, ROOT / 'build' / 'mygo-assets.zip', ROOT / 'web' / 'mygo-bundle.js')
    notices = go_notices(args.executable)
    folder = f'RF4S-Save-Editor-{version}'
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'w', ZIP_DEFLATED, compresslevel=9) as package:
        package.write(args.executable, f'{folder}/RF4S Save Editor.exe')
        readme = f'''# RF4S Save Editor {version}

Extract this folder and open **RF4S Save Editor.exe** on Windows 10/11 x64.
No installation, Python, Node, Qt or browser is needed. Game references,
item icons and Noto English/Chinese fonts are bundled for offline use.

Back up your entire save folder and close the game first. PC/Steam saves
are normally in `%APPDATA%\\Rune Factory 4 Special`. Open a slot file
(`rf4_sNN.sav`) for character/world edits, or `rf4_sys.sav` for player names
and persistent system unlocks, then edit values. Valid drafts apply before switching pages
or records and before export. Invalid drafts stay visible and block those
actions. Changes remain in memory until you explicitly export.

Choose the intended destination under **Review & export**. **Export edited
save** writes to `%APPDATA%\\Rune Factory 4 Special` after backing up its current
bytes. **Save as…** writes a separate copy or extracted Switch output.
The editor also accepts Switch saves already extracted from the console.
PC/Switch conversion is experimental and requires choosing the output
platform and checking its risk acknowledgement under Review & export.
It does not decrypt saves or transfer them to a console.
Backups & rollback retains up to ten matching editor backups per save.
Keep an independent full-folder backup and handle Steam Cloud separately.

A valid checksum does not guarantee gameplay compatibility. Experimental
story, romance and roster edits do not add missing scripts or world records.
No in-game acceptance testing is claimed. **Try synthetic demo** on Save
overview lets you explore without a personal save; demo export is disabled.

The extracted folder includes the [MyGO guide](docs/mygo-desktop.md) and
[release notes](RELEASE_NOTES.md) for controls and limitations.
Source: https://github.com/rikimtasu/rf4s_pc_saveedit/tree/{version}
'''
        package.writestr(f'{folder}/README.md', readme)
        for filename in ('RELEASE_NOTES.md', 'ATTRIBUTION.md'):
            package.write(ROOT / filename, f'{folder}/{filename}')
        for document in sorted((ROOT / 'docs').glob('*.md')):
            package.write(document, f'{folder}/docs/{document.name}')
        package.write(ROOT / 'COPYING', f'{folder}/licenses/Editor-GPL-3.0.txt')
        package.write(ROOT / 'vendor' / 'rf4-modkit' / 'LICENSE', f'{folder}/licenses/rf4-modkit-MIT.txt')
        package.writestr(f'{folder}/licenses/Game-assets-NOTICE.txt',
            'Game-derived reference text and icon images remain the property of the Rune Factory 4 Special rights holders. '
            'They are not relicensed under the editor GPL. No personal saves or full game archives are included.\n')
        for name in FONT_FILES - {'NotoSans.ttf', 'NotoSansCJKsc-Medium.otf'}:
            package.write(ROOT / 'web' / 'assets' / 'fonts' / name, f'{folder}/licenses/{name}')
        for name, data in notices.items():
            package.writestr(f'{folder}/licenses/{name}', data)
    output.with_suffix('.readme.md').write_text(readme, encoding='utf-8')
    notes = (ROOT / 'RELEASE_NOTES.md').read_text(encoding='utf-8').split('\n---\n', 1)[0]
    output.with_suffix('.notes.md').write_text(notes, encoding='utf-8')
    print(f'{output} ({output.stat().st_size / 1048576:.1f} MiB)')


if __name__ == '__main__':
    main()
