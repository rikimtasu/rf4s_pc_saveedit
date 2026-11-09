import importlib.util
from pathlib import Path
import struct
import unittest

AVAILABLE = all(importlib.util.find_spec(name) for name in ('PIL', 'pefile'))


@unittest.skipUnless(AVAILABLE, 'Build-time image dependencies are not installed')
class TextureTests(unittest.TestCase):
    def test_decoder_obeys_the_pixel_descriptor_and_excludes_relocation_bytes(self):
        from scripts.generate_builtin import texture_image
        data = bytearray(512)
        data[:4] = b'RES\0'; data[64:68] = b'PIXL'
        struct.pack_into('<II', data, 100, 4, 4)
        struct.pack_into('<I', data, 144, 16)
        struct.pack_into('<I', data, 48, 240)
        struct.pack_into('<I', data, 16, 272)
        image = texture_image(data)
        self.assertEqual(image.size, (4, 4))
        struct.pack_into('<I', data, 144, 999)
        with self.assertRaises(ValueError): texture_image(data)

    def test_non_resource_images_are_rejected(self):
        from scripts.generate_builtin import texture_image
        with self.assertRaises(ValueError): texture_image(b'not a texture')
