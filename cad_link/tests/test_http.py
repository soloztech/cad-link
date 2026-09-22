# SPDX-License-Identifier: LGPL-3.0-or-later
import errno
from unittest.mock import patch

from odoo.tests import HttpCase, tagged

from .common import CadFixture


class ProviderError(OSError):
    """Simulate SMB errors without OSError's built-in subclass selection."""


@tagged("post_install", "-at_install")
class TestCadHttp(CadFixture, HttpCase):
    def url(self, filename=None):
        path = "/cad-link/product/%s" % self.product.id
        if filename:
            path += "/file/" + filename
        return path + "?company_id=%s" % self.company.id

    def test_authenticated_listing_and_pdf(self):
        self.authenticate(self.reader.login, self.reader.login)
        response = self.url_open(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertIn("000001.pdf", response.text)
        self.assertNotIn("000001.ipt", response.text)
        response = self.url_open(self.url("000001.pdf"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/pdf")
        self.assertTrue(response.headers["Content-Disposition"].startswith("inline;"))
        self.assertEqual(response.headers["Cache-Control"], "private, no-store")

    def test_direct_native_url_is_denied(self):
        self.authenticate(self.reader.login, self.reader.login)
        self.assertEqual(self.url_open(self.url("000001.ipt")).status_code, 403)

    def _check_provider_error(self, error_number, status):
        details = "private-host.example/private-share secret=synthetic-provider-secret"
        error = ProviderError(error_number, details)
        self.assertNotIsInstance(error, (FileNotFoundError, PermissionError, NotADirectoryError))
        for filename in (None, "000001.pdf"):
            with self.subTest(errno=error_number, filename=filename), patch.object(
                type(self.storage.fs), "info", side_effect=error,
            ) as provider_info:
                response = self.url_open(self.url(filename))
                provider_info.assert_called()
                self.assertEqual(response.status_code, status)
                for private_value in ("private-host", "private-share", "synthetic-provider-secret"):
                    self.assertNotIn(private_value, response.text)

    def test_provider_missing_path_is_not_found(self):
        self.authenticate(self.reader.login, self.reader.login)
        for error_number in (errno.ENOENT, errno.ENOTDIR):
            self._check_provider_error(error_number, 404)

    def test_provider_permission_failure_is_forbidden(self):
        self.authenticate(self.reader.login, self.reader.login)
        for error_number in (errno.EACCES, errno.EPERM):
            self._check_provider_error(error_number, 403)

    def test_other_provider_failure_is_unavailable(self):
        self.authenticate(self.reader.login, self.reader.login)
        self._check_provider_error(errno.EIO, 503)

    def test_unauthorized_user_is_denied(self):
        self.authenticate(self.outsider.login, self.outsider.login)
        self.assertEqual(self.url_open(self.url()).status_code, 403)

    def test_source_download_and_company_boundary(self):
        self.authenticate(self.engineer.login, self.engineer.login)
        response = self.url_open(self.url("000001.ipt"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["Content-Disposition"].startswith("attachment;"))
        self.assertEqual(self.url_open(self.url().replace("company_id=%s" % self.company.id,
                                                          "company_id=2147483647")).status_code, 403)
