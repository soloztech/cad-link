# SPDX-License-Identifier: LGPL-3.0-or-later
import errno
import logging
from urllib.parse import quote, urlencode

from odoo import _, http
from odoo.exceptions import AccessError, UserError
from odoo.http import content_disposition, request
from werkzeug.exceptions import BadRequest, Forbidden, NotFound, ServiceUnavailable

_logger = logging.getLogger(__name__)


class CadDocuments(http.Controller):
    def _product(self, product_id, company_id):
        try:
            company_id = int(company_id)
        except (TypeError, ValueError) as error:
            raise BadRequest("A company is required") from error
        if company_id not in request.env.user.company_ids.ids:
            raise Forbidden()
        return request.env["product.product"].with_context(
            allowed_company_ids=[company_id],
        ).browse(product_id)

    def _error(self, error):
        # SMB providers can raise plain OSError subclasses rather than Python's
        # specific filesystem exceptions. Never expose their message to users.
        provider_errno = error.errno if isinstance(error, OSError) else None
        if isinstance(error, (AccessError, PermissionError)) or provider_errno in (
            errno.EACCES, errno.EPERM,
        ):
            raise Forbidden() from error
        if isinstance(error, (FileNotFoundError, NotADirectoryError)) or provider_errno in (
            errno.ENOENT, errno.ENOTDIR,
        ):
            raise NotFound(_("The item folder or document does not exist.")) from error
        if isinstance(error, UserError):
            raise BadRequest(str(error)) from error
        # Provider messages may contain credentials/host details. Never return
        # or log exception strings or a provider traceback.
        _logger.warning("CAD storage operation failed (%s)", type(error).__name__)
        raise ServiceUnavailable(_("CAD storage is temporarily unavailable.")) from None

    @http.route("/cad-link/product/<int:product_id>", type="http", auth="user", methods=["GET"])
    def documents(self, product_id, company_id=None, **kwargs):
        product = self._product(product_id, company_id)
        try:
            rows = product._cad_list_documents()
        except Exception as error:
            self._error(error)
        query = urlencode({"company_id": int(company_id)})
        for row in rows:
            row["url"] = "/cad-link/product/%s/file/%s?%s" % (
                product.id, quote(row["name"], safe=""), query,
            )
        response = request.render("cad_link.document_list", {
            "product": product, "documents": rows,
        })
        response.headers["Cache-Control"] = "private, no-store"
        return response

    @http.route(
        "/cad-link/product/<int:product_id>/file/<string:filename>",
        type="http", auth="user", methods=["GET"],
    )
    def document(self, product_id, filename, company_id=None, download=None, **kwargs):
        product = self._product(product_id, company_id)
        try:
            data, kind = product._cad_read_document(filename)
        except Exception as error:
            self._error(error)
        disposition = content_disposition(filename)
        if kind == "pdf" and download != "1":
            disposition = disposition.replace("attachment;", "inline;", 1)
        return request.make_response(data, headers=[
            ("Content-Type", "application/pdf" if kind == "pdf" else "application/octet-stream"),
            ("Content-Disposition", disposition),
            ("Cache-Control", "private, no-store"),
            ("X-Content-Type-Options", "nosniff"),
            ("X-Frame-Options", "SAMEORIGIN"),
            ("Content-Security-Policy", "sandbox"),
        ])

    @http.route(
        "/cad-link/product/<int:product_id>/viewer/<string:filename>",
        type="http", auth="user", methods=["GET"],
    )
    def viewer(self, product_id, filename, company_id=None, **kwargs):
        product = self._product(product_id, company_id)
        try:
            product._cad_preview_context(filename)
        except Exception as error:
            self._error(error)
        model_path = "/cad-link/product/%s/preview/%s" % (product.id, quote(filename, safe=""))
        model_url = model_path + "?" + urlencode({"company_id": int(company_id)})
        response = request.render("cad_link.viewer", {"filename": filename, "model_url": model_url})
        # This fixed iframe never loads backend assets or remote services. The
        # only fetch destination is its authorized, validated GLB endpoint.
        model_source = request.httprequest.host_url.rstrip("/") + model_path
        response.headers.update({
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": (
                "default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; "
                "img-src blob: data:; connect-src %s blob:; worker-src 'none'; "
                "object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'"
            ) % model_source,
        })
        return response

    @http.route(
        "/cad-link/product/<int:product_id>/preview/<string:filename>",
        type="http", auth="user", methods=["GET"],
    )
    def preview(self, product_id, filename, company_id=None, **kwargs):
        product = self._product(product_id, company_id)
        try:
            data = product._cad_read_preview(filename)
        except Exception as error:
            self._error(error)
        return request.make_response(data, headers=[
            ("Content-Type", "model/gltf-binary"),
            ("Content-Disposition", content_disposition(filename).replace("attachment;", "inline;", 1)),
            ("Cache-Control", "private, no-store"),
            ("X-Content-Type-Options", "nosniff"),
            ("Content-Security-Policy", "sandbox"),
        ])
