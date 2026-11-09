"""Export-to-game-code tests. Set RF4S_EXE to the audited executable."""
import base64
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXECUTABLE = os.environ.get('RF4S_EXE')
AVAILABLE = bool(EXECUTABLE) and all(importlib.util.find_spec(name) for name in ('pefile', 'capstone', 'unicorn'))


@unittest.skipUnless(AVAILABLE, 'Set RF4S_EXE and install read-only replay dependencies')
class FriendshipReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from replay_friendship import FriendshipReplay
        cls.replay = FriendshipReplay(Path(EXECUTABLE))

    def exports(self, edits):
        program = """
            import {createDemo} from './web/save-core.js';
            import {ExtendedSave} from './web/extended-core.js';
            const outputs = JSON.parse(process.argv[1]).map(edits => {
                const save = createDemo();
                const editor = new ExtendedSave(save);
                for (const [id, level] of edits) editor.setFriendship(id, level);
                return Buffer.from(save.build()).toString('base64');
            });
            process.stdout.write(JSON.stringify(outputs));
        """
        output = subprocess.check_output(['node', '--input-type=module', '-e', program, json.dumps(edits)], cwd=ROOT)
        return [base64.b64decode(value) for value in json.loads(output)]

    def test_barrett_and_raven_exports_reach_requested_levels_in_game_code(self):
        edits = [[[24, 10], [25, 27]], [[24, 0], [25, 10000]], [[24, 10000], [25, 0]]]
        for targets, data in zip(edits, self.exports(edits)):
            self.replay.load(data)
            for npc, level in targets:
                with self.subTest(npc=npc, level=level):
                    self.assertEqual(self.replay.level(npc), level)

    def test_every_main_npc_export_reaches_its_own_requested_level(self):
        targets = [[npc, npc * 13] for npc in range(1, 24)]
        self.replay.load(self.exports([targets])[0])
        for npc, level in targets:
            with self.subTest(npc=npc): self.assertEqual(self.replay.level(npc), level)

    def test_main_level_thresholds_match_actual_conversion_instructions(self):
        thresholds = [0, 16, 42, 83, 140, 226, 322, 429, 704, 1009, 1345]
        for level in range(10001):
            minimum = thresholds[level] if level <= 10 else level * 336 - 2015
            with self.subTest(level=level):
                self.assertEqual(self.replay.points_to_level(minimum), level)
                if level: self.assertEqual(self.replay.points_to_level(minimum - 1), level - 1)


if __name__ == '__main__': unittest.main()
