from pathlib import Path
import struct
import tempfile
import unittest

from scripts.game_sources import parse_text, parse_name_table, language_references, GameSource


class GameSourceTests(unittest.TestCase):
    def table(self, names):
        data = bytearray(b'TEXT' + struct.pack('<I', len(names)) + b'\0' * (len(names) * 8))
        for index, name in enumerate(names):
            value = name.encode('utf-8')
            struct.pack_into('<II', data, 8 + index * 8, len(value), len(data))
            data += value + b'\0'
        return data

    def test_text_bounds_and_utf8(self):
        names = ['None', 'キャベツ', '卷心菜', '양배추']
        data = self.table(names)
        self.assertEqual(parse_text(data), names)
        with self.assertRaises(ValueError):
            parse_text(data[:-1])
        struct.pack_into('<I', data, 12, 0)
        with self.assertRaises(ValueError):
            parse_text(data)

    def test_only_available_languages_are_offered(self):
        data = self.table(['None', '卷心菜'])
        class Source:
            def read(self, name):
                return data if name == 'rf3TxtItem_split2_1.chn' else None
        languages = language_references(Source())['languages']
        self.assertEqual(list(languages), ['zh-Hans'])
        self.assertEqual(languages['zh-Hans']['items'][1], '卷心菜')

    def test_archive_path_and_bounds_are_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            source = object.__new__(GameSource)
            source.bundle = Path(temp)
            source.entries = [{'bundleName': '../outside', 'files': {'test.eng': {'offset': 0, 'size': 10}}}]
            with self.assertRaises(ValueError):
                source.read('test.eng')
            self.assertIsNone(source.read('missing.eng'))

    def test_nickname_tables_are_loaded_with_their_original_ids_and_tokens(self):
        names = [''] * 186; names[24] = '＠しゅじんこうくん＠'; names[97] = 'Master'; names[133] = 'Vin'
        data = self.table(names)
        class Source:
            def read(self, name):
                return data if name == 'rf3TxtHeroNickName.eng' else None
        refs = language_references(Source())['languages']['en']
        self.assertEqual(refs['nicknames'], names)
        with self.assertRaises(ValueError): parse_name_table('nicknames', self.table(['Unknown']))


if __name__ == '__main__':
    unittest.main()
