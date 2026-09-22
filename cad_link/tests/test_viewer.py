# SPDX-License-Identifier: LGPL-3.0-or-later
from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.tests import HttpCase, TransactionCase, tagged

from .common import CadFixture
from .glb_fixture import encode_glb, textured_document, textured_glb


class GlbFixture(CadFixture):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.glb = cls.folder / "000001.glb"
        cls.glb.write_bytes(textured_glb())


@tagged("post_install", "-at_install")
class TestCadViewer(GlbFixture, TransactionCase):
    def test_listing_offers_viewer_only_for_authorized_glb(self):
        rows = self.as_user(self.engineer).get_cad_documents()["documents"]
        self.assertEqual([row["name"] for row in rows if row["viewer_url"]], ["000001.glb"])
        self.assertTrue(all(row["download_url"] for row in rows))
        self.assertEqual([row["name"] for row in self.as_user(self.reader).get_cad_documents()["documents"]], ["000001.pdf"])

    def test_preview_preserves_embedded_texture_bytes(self):
        self.assertEqual(self.as_user(self.engineer)._cad_read_preview("000001.glb"), textured_glb())

    def test_preview_denied_before_storage(self):
        for user, name in ((self.reader, "000001.glb"), (self.outsider, "000001.glb"),
                           (self.engineer, "000001.ipt"), (self.engineer, "../000001.glb")):
            with self.subTest(user=user.login, filename=name), patch.object(type(self.product), "_cad_filesystem") as fs:
                with self.assertRaises(AccessError):
                    self.as_user(user)._cad_read_preview(name)
                fs.assert_not_called()

    def test_preview_record_rule_denied_before_storage(self):
        self.env["ir.rule"].create({
            "name": "Deny synthetic preview product", "model_id": self.env["ir.model"]._get_id("product.product"),
            "domain_force": "[('id', '!=', %d)]" % self.product.id,
        })
        with patch.object(type(self.product), "_cad_filesystem") as fs, self.assertRaises(AccessError):
            self.as_user(self.engineer)._cad_read_preview("000001.glb")
        fs.assert_not_called()


@tagged("post_install", "-at_install")
class TestCadViewerHttp(GlbFixture, HttpCase):
    def preview_url(self, route="preview", filename="000001.glb", company=None):
        return "/cad-link/product/%s/%s/%s?company_id=%s" % (
            self.product.id, route, filename, self.company.id if company is None else company,
        )

    def test_authenticated_frame_and_textured_model(self):
        self.authenticate(self.engineer.login, self.engineer.login)
        frame = self.url_open(self.preview_url("viewer"))
        self.assertEqual(frame.status_code, 200)
        self.assertIn("/cad_link/static/src/viewer.js", frame.text)
        self.assertNotIn("web.assets_backend", frame.text)
        policy = frame.headers["Content-Security-Policy"]
        self.assertIn("worker-src 'none'", policy)
        self.assertIn("/preview/000001.glb blob:;", policy)
        self.assertNotIn("'unsafe-eval'", policy)
        self.assertIn("'wasm-unsafe-eval'", policy)
        self.assertEqual(frame.headers["Cache-Control"], "private, no-store")
        response = self.url_open(self.preview_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "model/gltf-binary")
        self.assertEqual(response.headers["Cache-Control"], "private, no-store")
        self.assertEqual(response.content, textured_glb())

    def test_direct_preview_requires_source_group(self):
        for user in (self.reader, self.outsider):
            self.authenticate(user.login, user.login)
            for route in ("viewer", "preview"):
                with self.subTest(user=user.login, route=route), patch.object(type(self.storage.fs), "info") as info:
                    self.assertEqual(self.url_open(self.preview_url(route)).status_code, 403)
                    info.assert_not_called()

    def test_company_and_extension_boundary(self):
        self.authenticate(self.engineer.login, self.engineer.login)
        for route in ("viewer", "preview"):
            self.assertEqual(self.url_open(self.preview_url(route, company=2147483647)).status_code, 403)
            self.assertEqual(self.url_open(self.preview_url(route, filename="000001.ipt")).status_code, 403)

    def test_external_texture_is_rejected_but_download_remains(self):
        self.authenticate(self.engineer.login, self.engineer.login)
        document, binary = textured_document()
        document["images"][0]["uri"] = "https://private.example/secret-texture.png"
        self.glb.write_bytes(encode_glb(document, binary))
        try:
            response = self.url_open(self.preview_url())
            self.assertEqual(response.status_code, 400)
            self.assertNotIn("private.example", response.text)
            response = self.url_open(self.preview_url("file") + "&download=1")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.headers["Content-Disposition"].startswith("attachment;"))
        finally:
            self.glb.write_bytes(textured_glb())

    def test_current_file_is_read_again_and_size_limit_applies(self):
        self.authenticate(self.engineer.login, self.engineer.login)
        original = self.url_open(self.preview_url())
        document, binary = textured_document()
        document["asset"]["generator"] = "Updated synthetic preview"
        updated = encode_glb(document, binary)
        self.glb.write_bytes(updated)
        try:
            response = self.url_open(self.preview_url())
            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(response.content, original.content)
            self.assertEqual(response.content, updated)
            self.glb.write_bytes(b"x" * (1024 * 1024 + 1))
            self.assertEqual(self.url_open(self.preview_url()).status_code, 400)
        finally:
            self.glb.write_bytes(textured_glb())

    def test_missing_file_and_duplicate_reference(self):
        self.authenticate(self.engineer.login, self.engineer.login)
        self.assertEqual(self.url_open(self.preview_url(filename="missing.glb")).status_code, 404)
        self.env["product.product"].create({"name": "Preview duplicate", "default_code": "000001", "company_id": self.company.id})
        for route in ("viewer", "preview"):
            self.assertEqual(self.url_open(self.preview_url(route)).status_code, 400)
