# SPDX-License-Identifier: LGPL-3.0-or-later
import errno
from unittest.mock import patch
from urllib.parse import parse_qs, unquote, urlsplit

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged

from .common import CadFixture


@tagged("post_install", "-at_install")
class TestCadDocuments(CadFixture, TransactionCase):
    def test_inline_listing_keeps_download_without_desktop(self):
        payload = self.as_user(self.engineer).get_cad_documents()
        self.assertFalse(payload["desktop_enabled"])
        self.assertFalse(payload["folder_url"])
        self.assertEqual(payload["folder_path"], r"\\fileserver\CAD$\Items\000001")
        self.assertEqual(len(payload["documents"]), 2)
        for row in payload["documents"]:
            self.assertIn("company_id=%s" % self.company.id, row["download_url"])
            self.assertTrue(row["download_url"].endswith("&download=1"))
            self.assertFalse(row["open_url"])
            self.assertFalse(row["folder_url"])

    def test_inline_network_actions_preserve_pdf_group(self):
        self.company.cad_desktop_enabled = True
        payload = self.as_user(self.reader).get_cad_documents()
        self.assertEqual([row["name"] for row in payload["documents"]], ["000001.pdf"])
        row = payload["documents"][0]
        expected_file = r"\\fileserver\CAD$\Items\000001\000001.pdf"
        for action, url in (("open", row["open_url"]), ("folder", row["folder_url"])):
            parsed = urlsplit(url)
            self.assertEqual((parsed.scheme, parsed.netloc), ("cad-link", action))
            self.assertEqual(parse_qs(parsed.query), {"path": [expected_file]})
        self.assertEqual(parse_qs(urlsplit(payload["folder_url"]).query), {
            "path": [r"\\fileserver\CAD$\Items\000001"],
        })

    def test_inline_network_and_download_urls_encode_special_characters(self):
        self.company.cad_desktop_enabled = True
        name = "Ação + 1 & corte #2.pdf"
        file = self.folder / name
        file.write_bytes(b"%PDF-1.4\n%%EOF\n")
        try:
            rows = self.as_user(self.reader).get_cad_documents()["documents"]
            row = next(row for row in rows if row["name"] == name)
            for key in ("open_url", "folder_url"):
                self.assertNotIn("+", row[key])
                self.assertNotIn("#", row[key])
                self.assertNotIn(" ", row[key])
                self.assertEqual(parse_qs(urlsplit(row[key]).query), {
                    "path": [r"\\fileserver\CAD$\Items\000001" + "\\" + name],
                })
            self.assertTrue(unquote(urlsplit(row["download_url"]).path).endswith("/" + name))
        finally:
            file.unlink()

    def test_inline_access_checked_before_storage(self):
        with patch.object(type(self.product), "_cad_filesystem") as filesystem:
            with self.assertRaises(AccessError):
                self.as_user(self.outsider).get_cad_documents()
            filesystem.assert_not_called()

    def test_inline_record_rule_checked_before_storage(self):
        self.env["ir.rule"].create({
            "name": "Deny CAD inline synthetic product", "model_id": self.env["ir.model"]._get_id("product.product"),
            "domain_force": "[('id', '!=', %d)]" % self.product.id,
        })
        with patch.object(type(self.product), "_cad_filesystem") as filesystem:
            with self.assertRaises(AccessError):
                self.as_user(self.engineer).get_cad_documents()
            filesystem.assert_not_called()

    def test_inline_provider_errors_are_sanitized(self):
        detail = "secret=provider-token private-host/private-share"
        for error_number, expected_exception, message in (
            (errno.ENOENT, UserError, "does not exist"),
            (errno.ENOTDIR, UserError, "does not exist"),
            (errno.EACCES, AccessError, "denied"),
            (errno.EPERM, AccessError, "denied"),
            (errno.EIO, UserError, "temporarily unavailable"),
        ):
            with self.subTest(errno=error_number), patch.object(
                type(self.product), "_cad_list_documents", side_effect=OSError(error_number, detail),
            ), self.assertRaises(expected_exception) as error:
                self.as_user(self.engineer).get_cad_documents()
            self.assertIn(message, str(error.exception))
            self.assertNotIn(detail, str(error.exception))
        with patch.object(type(self.product), "_cad_list_documents", side_effect=RuntimeError(detail)), \
                self.assertRaises(UserError) as error:
            self.as_user(self.engineer).get_cad_documents()
        self.assertNotIn(detail, str(error.exception))

    def test_inline_missing_folder_is_explained(self):
        self.product.default_code = "MISSING"
        with self.assertRaisesRegex(UserError, "does not exist"):
            self.as_user(self.engineer).get_cad_documents()

    def test_inline_template_delegates_and_denies_unprivileged_user(self):
        template = self.product.product_tmpl_id
        payload = template.with_user(self.reader).get_cad_documents()
        self.assertEqual(payload["product_id"], self.product.id)
        self.assertEqual([row["name"] for row in payload["documents"]], ["000001.pdf"])
        with self.assertRaises(AccessError):
            template.with_user(self.outsider).get_cad_documents()

    def test_inline_other_company_denied(self):
        other = self.env["res.company"].create({"name": "Other inline synthetic company"})
        self.product.company_id = other
        for product in (self.product, self.product.product_tmpl_id):
            with self.subTest(model=product._name), self.assertRaises(AccessError):
                product.with_user(self.engineer).with_context(allowed_company_ids=[self.company.id]).get_cad_documents()

    def test_desktop_requires_windows_share(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.company.write({"cad_desktop_enabled": True, "cad_unc_root": False})

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
        with patch.object(type(self.product), "_cad_filesystem") as filesystem:
            self.assertEqual(template.with_user(self.reader).get_cad_documents(), {
                "select_variant": True, "documents": [],
            })
            filesystem.assert_not_called()
