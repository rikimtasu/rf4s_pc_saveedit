"""Optional export-to-game-code regression. Set RF4S_EXE to the audited build."""
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
class RelationshipReplayTests(unittest.TestCase):
    def export(self, clean):
        program = """
            import {createDemo} from './web/save-core.js';
            const save = createDemo();
            save.setNumber(0x1db48, 'u32', 0x400302);
            save.patchBytes(0x1db4c, '61');
            save.setNumber(0x1db54, 'u32', 133 << 7);
            const output = save.build({gender:'male', resetDating:process.argv[1] === 'true'});
            process.stdout.write(Buffer.from(output).toString('base64'));
        """
        data = base64.b64decode(subprocess.check_output(['node', '--input-type=module', '-e', program, str(clean).lower()], cwd=ROOT))
        from replay_relationships import replay
        return replay(Path(EXECUTABLE), data)

    def test_gender_only_export_still_selects_dating_and_master(self):
        result = self.export(False)
        self.assertEqual(result['storedGender'], 0)
        vishnal = result['people'][0]
        self.assertTrue(vishnal['dating'])
        self.assertEqual(vishnal['npcCallsPlayer'], 97)
        self.assertEqual(vishnal['playerCallsNpc'], 133)

    def test_cleanup_export_reaches_non_dating_and_default_addresses_in_game_code(self):
        result = self.export(True)
        for person in result['people']:
            if person['id'] in (1, 5, 8, 9, 15, 20):
                self.assertFalse(person['dating'])
                self.assertEqual(person['npcCallsPlayer'], 23 + person['id'])
                self.assertEqual(person['playerCallsNpc'], person['id'])

    def test_individual_dating_and_nickname_edits_reach_actual_game_queries(self):
        from replay_relationships import replay, NPC_NAMES
        for dating in [0, 1]:
            program = """
                import {createDemo} from './web/save-core.js';
                import {RelationshipEditor} from './web/relationship-core.js';
                const save = createDemo(), editor = new RelationshipEditor(save);
                for (const id of [1,2,4,5,7,8,9,11,13,15,17,20])
                    editor.apply(id, {dating:Number(process.argv[1]), npcCallsPlayer:97, playerCallsNpc:133});
                process.stdout.write(Buffer.from(save.build()).toString('base64'));
            """
            data = base64.b64decode(subprocess.check_output(['node', '--input-type=module', '-e', program, str(dating)], cwd=ROOT))
            result = replay(Path(EXECUTABLE), data)
            self.assertEqual(len(result['people']), len(NPC_NAMES))
            for person in result['people']:
                with self.subTest(npc=person['id'], dating=dating):
                    self.assertEqual(person['dating'], bool(dating))
                    self.assertEqual(person['npcCallsPlayer'], 97)
                    self.assertEqual(person['playerCallsNpc'], 133)

    def test_experimental_non_candidate_bits_reach_actual_dating_query(self):
        from replay_relationships import replay
        program = """
            import {createDemo} from './web/save-core.js';
            import {RelationshipEditor} from './web/relationship-core.js';
            const save = createDemo(), editor = new RelationshipEditor(save);
            for(let id=1;id<=23;id++) editor.apply(id,{dating:1},{experimental:true});
            process.stdout.write(Buffer.from(save.build()).toString('base64'));
        """
        data = base64.b64decode(subprocess.check_output(['node', '--input-type=module', '-e', program], cwd=ROOT))
        result = replay(Path(EXECUTABLE), data, {npc: f'NPC {npc}' for npc in range(1, 24)})
        self.assertEqual(len(result['people']), 23)
        self.assertTrue(all(person['dating'] for person in result['people']))


if __name__ == '__main__':
    unittest.main()
