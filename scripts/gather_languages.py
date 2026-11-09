"""Extract localized names from the user's game; no game files are changed."""
import argparse
import json
from pathlib import Path
from game_sources import ROOT, GameSource, language_references


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'web' / 'local-languages.js')
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.game.resolve()):
        parser.error('Output must be outside the game directory.')
    data = language_references(GameSource(args.game))
    if not data['languages']:
        parser.error('No supported game-language tables were found.')
    args.output.write_text('export const LOCAL_LANGUAGES = ' + json.dumps(data, ensure_ascii=True, separators=(',', ':')) + ';\n', encoding='utf-8')
    for code, language in data['languages'].items():
        print(f'{code}: ' + ', '.join(f'{key}={len(language[key])}' for key in ['items', 'people', 'skills'] if key in language))


if __name__ == '__main__':
    main()
