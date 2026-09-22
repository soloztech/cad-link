# SPDX-License-Identifier: LGPL-3.0-or-later
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged

from .common import CadFixture


@tagged("post_install", "-at_install")
class TestCadDocuments(CadFixture, TransactionCase):
    def test_pdf_only_access(self):
        product = self.as_user(self.reader)
        self.assertEqual([row["name"] for row in product._cad_list_documents()], ["000001.pdf"])
        self.assertTrue(product._cad_read_document("000001.pdf")[0].startswith(b"%PDF-"))
        with self.assertRaises(AccessError):
            product._cad_read_document("000001.ipt")

    def test_source_access_and_excluded_files(self):
        product = self.as_user(self.engineer)
        self.assertEqual(len(product._cad_list_documents()), 2)
        self.assertEqual(product._cad_read_document("000001.ipt")[1], "source")
        with self.assertRaises(AccessError):
            product._cad_read_document("private.env")

    def test_no_group_no_access(self):
        product = self.as_user(self.outsider)
        with self.assertRaises(AccessError):
            product.action_open_cad_documents()
        with self.assertRaises(AccessError):
            product._cad_read_document("000001.pdf")

    def test_no_config_disclosure(self):
        with self.assertRaises(AccessError):
            self.company.with_user(self.reader).read(["cad_storage_id"])
        with self.assertRaises(AccessError):
            self.storage.with_user(self.reader).read(["options"])

    def test_product_record_rule_respected(self):
        self.env["ir.rule"].create({
            "name": "Deny synthetic CAD product", "model_id": self.env["ir.model"]._get_id("product.product"),
            "domain_force": "[('id', '!=', %d)]" % self.product.id,
        })
        with self.assertRaises(AccessError):
            self.as_user(self.reader)._cad_read_document("000001.pdf")

    def test_leading_zero_and_unc(self):
        product = self.as_user(self.reader)
        self.assertEqual(product.cad_folder_path, r"\\fileserver\CAD$\Items\000001")
        self.assertIn("company_id=%s" % self.company.id, product.action_open_cad_documents()["url"])

    def test_missing_code_and_folder(self):
        self.product.default_code = False
        with self.assertRaises(UserError):
            self.as_user(self.reader).action_open_cad_documents()
        self.product.default_code = "MISSING"
        with self.assertRaises(FileNotFoundError):
            self.as_user(self.reader)._cad_list_documents()

    def test_duplicate_code_including_inactive(self):
        duplicate = self.env["product.product"].create({
            "name": "Archived duplicate", "default_code": self.product.default_code,
            "company_id": self.company.id,
        })
        duplicate.active = False
        self.assertEqual(duplicate.default_code, self.product.default_code)
        with self.assertRaises(UserError):
            self.as_user(self.reader)._cad_context()

    def test_case_insensitive_duplicate_and_literal_underscore(self):
        self.product.default_code = "P_100"
        self.env["product.product"].create({"name": "Different code", "default_code": "Pa100"})
        self.as_user(self.reader)._cad_context()
        self.env["product.product"].create({"name": "Case duplicate", "default_code": "p_100"})
        with self.assertRaises(UserError):
            self.as_user(self.reader)._cad_context()

    def test_other_company_denied(self):
        other = self.env["res.company"].create({"name": "Other synthetic company"})
        self.product.company_id = other
        with self.assertRaises(AccessError):
            self.as_user(self.reader)._cad_context()

    def test_traversal_denied(self):
        for name in ["../000001.pdf", "/etc/passwd", "a\\b.pdf", "000001.pdf:secret"]:
            with self.subTest(name=name), self.assertRaises(AccessError):
                self.as_user(self.engineer)._cad_read_document(name)

    def test_symlink_denied(self):
        target = self.root / "outside.pdf"
        target.write_bytes(b"%PDF-1.4\n")
        link = self.folder / "linked.pdf"
        link.symlink_to(target)
        try:
            with self.assertRaises(AccessError):
                self.as_user(self.reader)._cad_read_document("linked.pdf")
        finally:
            link.unlink()

    def test_file_size_and_pdf_signature(self):
        bad = self.folder / "bad.pdf"
        bad.write_bytes(b"<html>not a PDF</html>")
        try:
            with self.assertRaises(UserError):
                self.as_user(self.reader)._cad_read_document("bad.pdf")
            bad.write_bytes(b"%PDF-" + b"x" * (1024 * 1024))
            with self.assertRaises(UserError):
                self.as_user(self.reader)._cad_read_document("bad.pdf")
        finally:
            bad.unlink()

    def test_invalid_configuration(self):
        for values in [{"cad_items_directory": "../outside"}, {"cad_max_file_mb": 0},
                       {"cad_unc_root": "file:///private"}]:
            with self.subTest(values=values), self.assertRaises(ValidationError), self.cr.savepoint():
                self.company.write(values)

    def test_single_variant_template_delegates(self):
        action = self.product.product_tmpl_id.with_user(self.reader).action_open_cad_documents()
        self.assertIn("/cad-link/product/%s?" % self.product.id, action["url"])

    def test_multiple_variants_keep_distinct_folders(self):
        attribute = self.env["product.attribute"].create({"name": "Synthetic height"})
        values = self.env["product.attribute.value"].create([
            {"name": "2200", "attribute_id": attribute.id},
            {"name": "2500", "attribute_id": attribute.id},
        ])
        template = self.env["product.template"].create({
            "name": "Synthetic pillar variants",
            "attribute_line_ids": [(0, 0, {"attribute_id": attribute.id, "value_ids": [(6, 0, values.ids)]})],
        })
        variants = template.product_variant_ids.sorted("id")
        self.assertEqual(len(variants), 2)
        for product, code in zip(variants, ["P-2200", "P-2500"]):
            product.default_code = code
            self.assertEqual(product.with_user(self.reader)._cad_context()[1], "Items/" + code)
        action = template.with_user(self.reader).action_open_cad_documents()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["domain"], [("product_tmpl_id", "=", template.id)])
