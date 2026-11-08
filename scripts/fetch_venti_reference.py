"""Fetch documented table references through Codefloe's public contents API."""
import base64
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '6588b5ff7c28ddd82fd5b2a4591486af3e9c901a'
API = 'https://codefloe.com/api/v1/repos/droopy_dingo/venti'


def request(path):
    with urlopen(Request(API + path, headers={'User-Agent': 'RF4S-local-editor-reference'}), timeout=60) as response:
        return json.load(response)


def fetch(path):
    record = request(f'/contents/{path}?ref={COMMIT}')
    output = ROOT / 'vendor' / 'venti' / path
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(base64.b64decode(record['content']))
    return path


def main():
    tree = request(f'/git/trees/{COMMIT}?recursive=true')['tree']
    paths = [entry['path'] for entry in tree if entry['type'] == 'blob' and (
        entry['path'].startswith('src/rf/') or entry['path'] in (
            'README.md', 'LICENSE', 'src/hooks/config_data_hook.cpp'
        ))]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for path in pool.map(fetch, paths):
            print(path, flush=True)


if __name__ == '__main__':
    main()
