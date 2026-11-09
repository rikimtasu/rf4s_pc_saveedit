"""Optional actual-game-code tests for player-name edit/reset and system flags."""
import base64
import importlib.util
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXECUTABLE = os.environ.get('RF4S_EXE')
AVAILABLE = bool(EXECUTABLE) and all(importlib.util.find_spec(name) for name in ('pefile', 'capstone', 'unicorn'))


@unittest.skipUnless(AVAILABLE, 'Set RF4S_EXE and install read-only replay dependencies')
class PlayerNameReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from replay_player_names import PlayerNameReplay
        cls.replay = PlayerNameReplay(Path(EXECUTABLE))

    def export(self, name):
        program = """
            import {SaveDocument,crc32} from './web/save-core.js';
            import {PlayerNameEditor} from './web/player-name-core.js';
            const bytes = new Uint8Array(9304), view = new DataView(bytes.buffer);
            bytes.set(new TextEncoder().encode('RF4D'));
            view.setUint32(8, 0xfffff, true); view.setUint32(12, 0xfffff, true);
            view.setUint32(4, crc32(bytes.subarray(8)), true);
            const save = new SaveDocument(bytes), editor = new PlayerNameEditor(save);
            for (let i=0;i<40;i++) editor.apply(i, process.argv[1]);
            save.setSystemFlags({5:1});
            process.stdout.write(Buffer.from(save.build()).toString('base64'));
        """
        return base64.b64decode(subprocess.check_output(['node', '--input-type=module', '-e', program, name], cwd=ROOT))

    def test_all_system_record_names_reach_the_actual_slot_name_loader(self):
        data = self.export('芙蕾A')
        self.replay.load(data)
        for record in range(40):
            with self.subTest(record=record): self.assertEqual(self.replay.name(record), '芙蕾A')

    def test_reset_reaches_actual_default_name_branches_for_both_genders(self):
        self.replay.load(self.export(''))
        for record in [0, 19, 20, 39]:
            for gender, english, japanese in [('male', 'Lest', 'レスト'), ('female', 'Frey', 'フレイ')]:
                with self.subTest(record=record, gender=gender):
                    self.assertEqual(self.replay.name(record, gender), english)
                    self.assertEqual(self.replay.name(record, gender, japanese=True), japanese)

    def test_system_unlock_edits_reach_the_actual_script_getter(self):
        self.replay.load(self.export('Name'))
        self.assertTrue(self.replay.transfer_unlocked())


if __name__ == '__main__': unittest.main()
