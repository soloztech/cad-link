#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Check Python/XML syntax and manifest data paths without importing Odoo."""
import ast
from pathlib import Path
from xml.etree import ElementTree

root = Path(__file__).resolve().parents[1]
python_files = [*root.joinpath("cad_link").rglob("*.py"), *root.joinpath("tests").rglob("*.py")]
xml_files = list(root.joinpath("cad_link").rglob("*.xml"))
for path in python_files:
    ast.parse(path.read_text(), filename=str(path))
for path in xml_files:
    ElementTree.parse(path)
manifest = ast.literal_eval(root.joinpath("cad_link/__manifest__.py").read_text())
for path in manifest["data"]:
    assert root.joinpath("cad_link", path).is_file(), path
for paths in manifest.get("assets", {}).values():
    for path in paths:
        assert root.joinpath(path).is_file(), path
print(f"Checked {len(python_files)} Python files, {len(xml_files)} XML files and manifest paths.")
