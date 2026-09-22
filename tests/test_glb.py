# SPDX-License-Identifier: LGPL-3.0-or-later
import importlib.util
from pathlib import Path
import struct
import unittest


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


glb = load("cad_glb", "cad_link/glb.py")
fixtures = load("cad_glb_fixtures", "cad_link/tests/glb_fixture.py")


class TestGlb(unittest.TestCase):
    def test_embedded_texture_is_preserved(self):
        document = glb.validate_glb(fixtures.textured_glb())
        self.assertEqual(document["images"], [{"bufferView": 4, "mimeType": "image/png"}])
        self.assertEqual(document["materials"][0]["pbrMetallicRoughness"]["baseColorTexture"], {"index": 0})

    def test_header_chunk_and_truncation_rejected(self):
        data = fixtures.textured_glb()
        for bad in (b"", b"glTF", b"FAIL" + data[4:], data[:4] + struct.pack("<I", 1) + data[8:],
                    data[:-1], data + b"x", data[:12] + struct.pack("<I", 5) + data[16:],
                    data[:16] + b"BIN\x00" + data[20:]):
            with self.subTest(size=len(bad)), self.assertRaises(ValueError):
                glb.validate_glb(bad)

    def test_any_resource_uri_is_rejected(self):
        for uri in ("https://example.invalid/a.bin", "/web/session/logout", "file:///share/a", "data:image/png;base64,AA=="):
            for location in ("buffers", "images"):
                document, binary = fixtures.textured_document()
                document[location][0]["uri"] = uri
                with self.subTest(uri=uri, location=location), self.assertRaises(ValueError):
                    glb.validate_glb(fixtures.encode_glb(document, binary))

    def test_compressed_or_unknown_extensions_are_rejected(self):
        for extension in ("KHR_draco_mesh_compression", "EXT_meshopt_compression", "KHR_texture_basisu", "VENDOR_unknown"):
            for declaration in ("extensionsUsed", "extensionsRequired", "extensions"):
                document, binary = fixtures.textured_document()
                document[declaration] = {extension: {}} if declaration == "extensions" else [extension]
                with self.subTest(extension=extension, declaration=declaration), self.assertRaises(ValueError):
                    glb.validate_glb(fixtures.encode_glb(document, binary))

    def test_embedded_buffer_bounds(self):
        for key, value in (("byteOffset", -1), ("byteOffset", 999999), ("byteLength", 999999), ("buffer", 1), ("buffer", False)):
            document, binary = fixtures.textured_document()
            document["bufferViews"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                glb.validate_glb(fixtures.encode_glb(document, binary))

    def test_image_type_signature_and_reference(self):
        for values in ({"mimeType": "image/svg+xml"}, {"mimeType": "image/jpeg"}, {"bufferView": 99}, {"bufferView": True}):
            document, binary = fixtures.textured_document()
            document["images"][0].update(values)
            with self.subTest(values=values), self.assertRaises(ValueError):
                glb.validate_glb(fixtures.encode_glb(document, binary))

    def test_no_external_decoder_for_safe_material_extension(self):
        document, binary = fixtures.textured_document()
        document["extensionsUsed"] = ["KHR_materials_unlit"]
        document["materials"][0]["extensions"] = {"KHR_materials_unlit": {}}
        self.assertEqual(glb.validate_glb(fixtures.encode_glb(document, binary)), document)

    def test_duplicate_json_key_is_rejected(self):
        data = fixtures.textured_glb()
        marker = b'"scene":0'
        duplicated = data[20:20 + struct.unpack_from("<I", data, 12)[0]].rstrip().replace(marker, marker + b',"scene":1')
        duplicated += b" " * (-len(duplicated) % 4)
        binary_offset = 20 + struct.unpack_from("<I", data, 12)[0]
        bad = struct.pack("<4sII", b"glTF", 2, 20 + len(duplicated) + len(data[binary_offset:]))
        bad += struct.pack("<I4s", len(duplicated), b"JSON") + duplicated + data[binary_offset:]
        with self.assertRaises(ValueError):
            glb.validate_glb(bad)


if __name__ == "__main__":
    unittest.main()
