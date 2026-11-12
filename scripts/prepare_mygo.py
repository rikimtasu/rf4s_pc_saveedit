"""Pack offline MyGO assets using only Python's standard library."""
import ast
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent.parent


def main():
    output = ROOT / 'build' / 'mygo-assets.zip'
    output.parent.mkdir(exist_ok=True)
    tree = ast.parse((ROOT / 'native_i18n.py').read_text(encoding='utf-8'))
    catalog = next(ast.literal_eval(node.value) for node in tree.body
                   if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ZH' for t in node.targets))
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('zh.json', json.dumps(catalog, ensure_ascii=False))
        for path in (ROOT / 'web' / 'assets' / 'fonts').iterdir():
            if path.suffix in ('.ttf', '.otf', '.txt', '.md'):
                archive.write(path, 'fonts/' + path.name)
        for name in ('references.json.gz', 'icons.zip'):
            path = ROOT / 'builtin' / name
            if path.is_file():
                archive.write(path, name)
            else:
                print(f'Note: builtin/{name} absent; generated game references will not be bundled.')
    print(output)


if __name__ == '__main__':
    main()
