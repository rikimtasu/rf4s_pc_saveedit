"""Optional machine-code replay checks. Set RF4S_EXE to the audited executable.

These tests describe the appearance branch's limits, not NPC-dialogue acceptance.
The executable and synthetic save bytes are read-only / in-memory respectively.
"""
import importlib.util
import os
from pathlib import Path
import struct
import unittest
import zlib


EXECUTABLE = os.environ.get('RF4S_EXE')
AVAILABLE = bool(EXECUTABLE) and all(importlib.util.find_spec(name) for name in ('pefile', 'capstone', 'unicorn'))


@unittest.skipUnless(AVAILABLE, 'Set RF4S_EXE and install read-only replay dependencies')
class AppearanceReplayTests(unittest.TestCase):
    def replay(self, saved_gender, initial_gender):
        from replay_appearance import replay
        data = bytearray(140424)
        data[0x36] = saved_gender
        struct.pack_into('<I', data, 0, zlib.crc32(data[4:-224]))
        before = bytes(data)
        result = replay(Path(EXECUTABLE), bytes(data), initial_gender)
        self.assertEqual(bytes(data), before)
        return result

    def test_saved_male_does_not_force_an_existing_female_actor_to_male(self):
        result = self.replay(0, 'female')
        self.assertEqual(result['initialActorGender'], 'female')
        self.assertEqual(result['actorGender'], 'female')
        self.assertEqual(result['bodyResource'], 0x4d1)
        self.assertEqual(result['portraitResource'], 0x4d2)
        self.assertEqual(result['calls'], [])

    def test_saved_male_preserves_a_male_actor(self):
        result = self.replay(0, 'male')
        self.assertEqual(result['actorGender'], 'male')
        self.assertEqual(result['bodyResource'], 0x4c1)
        self.assertEqual(result['portraitResource'], 0x4c2)

    def test_saved_female_switches_a_male_actor(self):
        result = self.replay(1, 'male')
        self.assertEqual(result['actorGender'], 'female')
        self.assertEqual(result['bodyResource'], 0x4d1)
        self.assertEqual(result['portraitResource'], 0x4d2)


if __name__ == '__main__':
    unittest.main()
