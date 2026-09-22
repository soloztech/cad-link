# SPDX-License-Identifier: LGPL-3.0-or-later
"""Bounded, self-contained GLB profile for the browser viewer (no Odoo imports).

This checks the container and resource boundary, not the complete glTF schema.
Unsupported geometry still produces a normal renderer error in the viewer.
"""
import json
import struct


SAFE_EXTENSIONS = frozenset({
    "KHR_materials_unlit", "KHR_texture_transform", "KHR_mesh_quantization",
    "KHR_materials_clearcoat", "KHR_materials_ior", "KHR_materials_specular",
    "KHR_materials_sheen", "KHR_materials_transmission", "KHR_materials_volume",
    "KHR_materials_emissive_strength", "KHR_materials_iridescence",
    "KHR_materials_anisotropy",
})
MAX_JSON_BYTES = 4 * 1024 * 1024


def _integer(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError("Invalid GLB integer")
    return value


def _object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate GLB JSON property")
        result[key] = value
    return result


def _resources(value, depth=0):
    if depth > 64:
        raise ValueError("GLB JSON nesting exceeds the preview limit")
    if isinstance(value, dict):
        if "uri" in value:
            raise ValueError("GLB preview requires embedded resources without URIs")
        extensions = value.get("extensions", {})
        if not isinstance(extensions, dict) or set(extensions) - SAFE_EXTENSIONS:
            raise ValueError("GLB preview uses an unsupported extension")
        for child in value.values():
            _resources(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _resources(child, depth + 1)


def validate_glb(data):
    """Return parsed JSON only if a GLB uses embedded BIN/PNG/JPEG resources.

    Unknown extensions (including Draco, Meshopt and Basis/KTX2) are rejected,
    whether optional or required, so the renderer cannot load remote decoders.
    Data URIs are also excluded: image resources must be inside the BIN chunk.
    """
    if len(data) < 20:
        raise ValueError("Not a valid GLB container")
    magic, version, length = struct.unpack_from("<4sII", data)
    if magic != b"glTF" or version != 2 or length != len(data):
        raise ValueError("Preview requires a complete GLB version 2 file")
    chunks = []
    offset = 12
    while offset < length:
        if length - offset < 8:
            raise ValueError("Truncated GLB chunk")
        size, kind = struct.unpack_from("<I4s", data, offset)
        offset += 8
        if size % 4 or offset + size > length:
            raise ValueError("Invalid GLB chunk size")
        chunks.append((kind, memoryview(data)[offset:offset + size]))
        if len(chunks) > 2:
            raise ValueError("Unexpected GLB chunks")
        offset += size
    if not chunks or chunks[0][0] != b"JSON" or len(chunks[0][1]) > MAX_JSON_BYTES:
        raise ValueError("Invalid or oversized GLB JSON chunk")
    if len(chunks) != 2 or chunks[1][0] != b"BIN\x00":
        raise ValueError("Preview requires an embedded GLB binary chunk")
    try:
        document = json.loads(bytes(chunks[0][1]).decode("utf-8"), object_pairs_hook=_object_pairs,
                              parse_constant=lambda unused: (_ for _ in ()).throw(ValueError("Invalid number")))
    except (UnicodeDecodeError, RecursionError) as error:
        raise ValueError("Invalid GLB JSON") from error
    if not isinstance(document, dict) or not isinstance(document.get("asset"), dict):
        raise ValueError("Missing GLB asset")
    if document["asset"].get("version") != "2.0" or document["asset"].get("minVersion", "2.0") != "2.0":
        raise ValueError("Unsupported GLB asset version")
    _resources(document)
    for key in ("extensionsUsed", "extensionsRequired"):
        values = document.get(key, [])
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise ValueError("Invalid GLB extension declaration")
        if set(values) - SAFE_EXTENSIONS:
            raise ValueError("GLB preview uses an unsupported extension")
    if set(document.get("extensionsRequired", [])) - set(document.get("extensionsUsed", [])):
        raise ValueError("Undeclared required GLB extension")
    buffers = document.get("buffers")
    if not isinstance(buffers, list) or len(buffers) != 1 or not isinstance(buffers[0], dict):
        raise ValueError("Preview requires one embedded GLB buffer")
    binary = chunks[1][1]
    buffer_length = _integer(buffers[0].get("byteLength"), 1)
    if not buffer_length <= len(binary) <= buffer_length + 3 or any(binary[buffer_length:]):
        raise ValueError("Invalid GLB buffer length or padding")
    views = document.get("bufferViews", [])
    if not isinstance(views, list):
        raise ValueError("Invalid GLB buffer views")
    for view in views:
        if not isinstance(view, dict) or type(view.get("buffer")) is not int or view["buffer"] != 0:
            raise ValueError("Invalid GLB buffer view")
        start = _integer(view.get("byteOffset", 0))
        size = _integer(view.get("byteLength"), 1)
        if start + size > buffer_length:
            raise ValueError("GLB buffer view is outside the embedded buffer")
    images = document.get("images", [])
    if not isinstance(images, list):
        raise ValueError("Invalid GLB images")
    for image in images:
        if not isinstance(image, dict):
            raise ValueError("Invalid GLB image")
        index = _integer(image.get("bufferView"))
        if index >= len(views) or image.get("mimeType") not in ("image/png", "image/jpeg"):
            raise ValueError("Preview images must be embedded PNG or JPEG")
        view = views[index]
        start = view.get("byteOffset", 0)
        content = binary[start:start + view["byteLength"]]
        signature = b"\x89PNG\r\n\x1a\n" if image["mimeType"] == "image/png" else b"\xff\xd8\xff"
        if bytes(content[:len(signature)]) != signature:
            raise ValueError("GLB image does not match its declared format")
    return document
