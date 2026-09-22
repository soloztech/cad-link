# SPDX-License-Identifier: LGPL-3.0-or-later
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
        if isinstance(error, AccessError):
            raise Forbidden() from error
        if isinstance(error, FileNotFoundError):
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
