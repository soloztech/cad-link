# SPDX-License-Identifier: LGPL-3.0-or-later
"""Portable paths. This module deliberately has no Odoo dependency."""
import re

PDF_EXTENSIONS = frozenset({"pdf"})
SOURCE_EXTENSIONS = frozenset({
    "ipt", "iam", "idw", "dwg", "dxf", "step", "stp", "iges", "igs",
    "sat", "stl", "obj", "mtl", "glb", "gltf",
})
_RESERVED = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", re.I)


def component(value):
    """Validate, never normalize an item code or filename into another one."""
    if not isinstance(value, str) or not value or len(value) > 255:
        raise ValueError("A nonempty path component is required")
    if value != value.strip() or value.startswith(".") or value.endswith("."):
        raise ValueError("Hidden, relative and ambiguous names are not supported")
    if any(ord(c) < 32 or ord(c) == 127 or c in '/\\:*?"<>|' for c in value):
        raise ValueError("The name contains a path separator or reserved character")
    if _RESERVED.match(value):
        raise ValueError("Reserved Windows device name")
    return value


def relative_directory(value):
    if not isinstance(value, str):
        raise ValueError("A relative directory is required")
    if not value:
        return ""
    return "/".join(component(part) for part in value.split("/"))


def item_directory(prefix, code):
    prefix = relative_directory(prefix)
    return "/".join(part for part in (prefix, component(code)) if part)


def unc_directory(root, relative):
    if not root:
        return ""
    root = root.rstrip("\\")
    if not root.startswith("\\\\"):
        raise ValueError("Use a UNC root, such as \\\\fileserver\\CAD$")
    parts = root[2:].split("\\")
    if len(parts) < 2:
        raise ValueError("A UNC server and share are required")
    for part in parts:
        component(part)
    relative = relative_directory(relative)
    return root + ("\\" + relative.replace("/", "\\") if relative else "")


def document_kind(filename, allow_sources=False):
    filename = component(filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension in PDF_EXTENSIONS:
        return "pdf"
    if allow_sources and extension in SOURCE_EXTENSIONS:
        return "source"
    return None
