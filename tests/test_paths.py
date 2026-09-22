# SPDX-License-Identifier: LGPL-3.0-or-later
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("cad_paths", Path(__file__).parents[1] / "cad_link/paths.py")
paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paths)


class TestPaths(unittest.TestCase):
    def test_preserve_internal_reference(self):
        self.assertEqual(paths.item_directory("Items", "000001"), "Items/000001")
        self.assertEqual(paths.item_directory("", "P-2500"), "P-2500")
        self.assertEqual(paths.item_directory("Engineering/Items", "A_01"), "Engineering/Items/A_01")

    def test_reject_unsafe_components(self):
        for value in [None, "", ".", "..", "../secret", "a/b", "a\\b", "A:", "x\x00y", " x", "x ",
                      "x.", ".hidden", "x\ny", "a?b", "a*b", "CON", "aux.pdf", "LPT1.ipt", "x" * 256]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                paths.component(value)

    def test_reject_absolute_and_ambiguous_prefixes(self):
        for value in ["/Items", "Items/", "A//B", "A/../B", "C:/Items", "\\\\host\\share"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                paths.relative_directory(value)

    def test_unc_equivalence(self):
        self.assertEqual(paths.unc_directory(r"\\fileserver\CAD$", "Items/000001"),
                         r"\\fileserver\CAD$\Items\000001")
        self.assertEqual(paths.unc_directory("", "Items/000001"), "")
        for root in ["R:", "file://host/share", r"\host\share", r"\\host", r"\\host\share\.."]:
            with self.subTest(root=root), self.assertRaises(ValueError):
                paths.unc_directory(root, "")

    def test_document_permissions_and_extension(self):
        self.assertEqual(paths.document_kind("000001.PDF"), "pdf")
        self.assertIsNone(paths.document_kind("000001.ipt"))
        self.assertEqual(paths.document_kind("000001.ipt", True), "source")
        for name in ["secret.env", "document.pdf.exe", "page.html", "image.svg", "README"]:
            self.assertIsNone(paths.document_kind(name, True))


if __name__ == "__main__":
    unittest.main()
