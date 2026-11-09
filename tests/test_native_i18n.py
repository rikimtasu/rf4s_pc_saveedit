import ast
from pathlib import Path
import unittest

from native_i18n import UiLanguage, ZH

ROOT = Path(__file__).resolve().parents[1]


class NativeTranslationTests(unittest.TestCase):
    def test_switch_and_dynamic_templates_preserve_identifiers(self):
        ui = UiLanguage('zh-CN')
        self.assertEqual(ui.text('Open save'), '打开存档')
        self.assertEqual(ui.text('Crafting attachment 3'), '制作附加材料 3')
        self.assertEqual(ui.text('Poison resistance'), '毒抗性')
        self.assertEqual(ui.text('Upgrade 2 · level 3'), '强化 2 · 等级 3')
        for raw in ['REG_MAIN_SCENARIO', '0x1DB40', r'C:\用户\rf4_s01.sav', 'Frey personal name']:
            self.assertEqual(ui.text(raw), raw)
        ui.code = 'en'
        self.assertEqual(ui.text('Open save'), 'Open save')

    def test_static_native_widget_captions_have_chinese_entries(self):
        tree = ast.parse((ROOT / 'native_ui.py').read_text(encoding='utf-8'))
        names = {'QLabel', 'QPushButton', 'QCheckBox', 'QGroupBox', 'QAction'}
        captions = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in names and node.args:
                value = node.args[0]
                if isinstance(value, ast.Constant) and isinstance(value.value, str) and value.value:
                    captions.add(value.value)
        self.assertTrue(captions)
        self.assertEqual(sorted(captions - ZH.keys()), [])


if __name__ == '__main__': unittest.main()
