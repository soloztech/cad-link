# SPDX-License-Identifier: LGPL-3.0-or-later
"""Synthetic textured square; generated from numbers, never from customer CAD."""
import json
import struct
import zlib


def encode_glb(document, binary):
    encoded = json.dumps(document, separators=(",", ":")).encode("utf-8")
    encoded += b" " * (-len(encoded) % 4)
    binary += b"\x00" * (-len(binary) % 4)
    return (struct.pack("<4sII", b"glTF", 2, 28 + len(encoded) + len(binary))
            + struct.pack("<I4s", len(encoded), b"JSON") + encoded
            + struct.pack("<I4s", len(binary), b"BIN\x00") + binary)


def textured_document():
    def png_chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    png = (b"\x89PNG\r\n\x1a\n"
           + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0))
           + png_chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00\x00\xff\x00\x00\x00\x00\xff\xff\xff\xff"))
           + png_chunk(b"IEND", b""))
    sections = [
        struct.pack("<12f", -.5, -.5, 0, .5, -.5, 0, .5, .5, 0, -.5, .5, 0),
        struct.pack("<12f", *([0, 0, 1] * 4)),
        struct.pack("<8f", 0, 0, 1, 0, 1, 1, 0, 1),
        struct.pack("<6H", 0, 1, 2, 0, 2, 3), png,
    ]
    binary = b""
    views = []
    for section in sections:
        views.append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(section)})
        binary += section + b"\x00" * (-len(section) % 4)
    document = {
        "asset": {"version": "2.0", "generator": "CAD-link synthetic test fixture"},
        "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}],
        "buffers": [{"byteLength": len(binary)}], "bufferViews": views,
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-.5, -.5, 0], "max": [.5, .5, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 4, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 4, "type": "VEC2"},
            {"bufferView": 3, "componentType": 5123, "count": 6, "type": "SCALAR"},
        ],
        "images": [{"bufferView": 4, "mimeType": "image/png"}],
        "samplers": [{"magFilter": 9728, "minFilter": 9728}],
        "textures": [{"source": 0, "sampler": 0}],
        "materials": [{"doubleSided": True, "pbrMetallicRoughness": {
            "baseColorTexture": {"index": 0}, "metallicFactor": 0, "roughnessFactor": .8,
        }}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2}, "indices": 3, "material": 0}]}],
    }
    return document, binary


def textured_glb():
    return encode_glb(*textured_document())
