# SPDX-License-Identifier: LGPL-3.0-or-later
import os
import posixpath
from urllib.parse import urlencode

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

from ..paths import component, document_kind, item_directory, unc_directory


class ProductProduct(models.Model):
    _inherit = "product.product"

    cad_folder_path = fields.Char(
        string="CAD folder", compute="_compute_cad_folder_path", groups="cad_link.group_cad_documents",
    )

    @api.depends("default_code", "company_id")
    @api.depends_context("company")
    def _compute_cad_folder_path(self):
        for product in self:
            company = (product.company_id or self.env.company).sudo()
            try:
                path = item_directory(company.cad_items_directory or "", product.default_code)
                product.cad_folder_path = unc_directory(company.cad_unc_root or "", path) or path
            except ValueError:
                product.cad_folder_path = False

    def _cad_context(self):
        self.ensure_one()
        if not self.env.user.has_group("cad_link.group_cad_documents"):
            raise AccessError(_("CAD document access is required."))
        self.check_access_rights("read")
        self.check_access_rule("read")
        if not self.exists():
            raise UserError(_("Product not found."))
        company = self.company_id or self.env.company
        if company not in self.env.companies:
            raise AccessError(_("The product company is not allowed."))
        # Configuration is administrative. Elevation applies only after product
        # and company checks; never expose FS Storage options/credentials.
        config = company.sudo()
        if not config.cad_storage_id:
            raise UserError(_("Configure CAD storage on the company first."))
        try:
            path = item_directory(config.cad_items_directory or "", self.default_code)
        except ValueError as error:
            raise UserError(_("Set a valid, unambiguous internal reference on this variant.")) from error
        # SMB names are commonly case-insensitive. Escape SQL LIKE wildcards
        # without stripping or converting the actual item code.
        code_pattern = self.default_code.replace("%", r"\%").replace("_", r"\_")
        duplicates = self.sudo().with_context(active_test=False).search_count([
            ("default_code", "=ilike", code_pattern), ("id", "!=", self.id),
            ("company_id", "in", [False, company.id]),
        ])
        if duplicates:
            raise UserError(_("The internal reference is duplicated. Resolve it before opening CAD files."))
        return config, path

    def action_open_cad_documents(self):
        company, unused_path = self._cad_context()
        return {
            "type": "ir.actions.act_url", "target": "new",
            "url": "/cad-link/product/%s?%s" % (self.id, urlencode({"company_id": company.id})),
        }

    def _cad_filesystem(self, company):
        storage = company.cad_storage_id
        if storage.protocol not in ("smb", "file"):
            raise UserError(_("Unsupported CAD storage protocol."))
        return storage.fs

    def _cad_info(self, fs, company, path):
        """Check parent directories too; do not follow symlinks/reparse links."""
        storage = company.cad_storage_id
        if storage.protocol == "file":
            root = os.path.abspath(storage.get_directory_path() or ".")
            target = os.path.join(root, path)
            if os.path.realpath(root) != root or os.path.realpath(target) != target:
                raise AccessError(_("CAD symbolic links are not supported."))
            if os.path.commonpath([root, target]) != root:
                raise AccessError(_("Invalid CAD path."))
        checked = ""
        for part in path.split("/"):
            checked = posixpath.join(checked, component(part))
            info = fs.info(checked, follow_symlinks=False)
            if info.get("type") == "link" or info.get("islink"):
                raise AccessError(_("CAD symbolic links are not supported."))
            if checked != path and info.get("type") != "directory":
                raise AccessError(_("Invalid CAD directory."))
        return info

    def _cad_list_documents(self):
        company, folder = self._cad_context()
        fs = self._cad_filesystem(company)
        if self._cad_info(fs, company, folder).get("type") != "directory":
            raise UserError(_("The CAD item path is not a directory."))
        fs.invalidate_cache(folder)
        paths = fs.ls(folder, detail=False)
        if len(paths) > 500:
            raise UserError(_("This item folder exceeds the 500-entry limit."))
        sources = self.env.user.has_group("cad_link.group_cad_sources")
        documents = []
        for path in paths:
            name = posixpath.basename(path.rstrip("/"))
            try:
                kind = document_kind(name, sources)
            except ValueError:
                continue
            if not kind:
                continue
            info = self._cad_info(fs, company, posixpath.join(folder, name))
            if info.get("type") == "file":
                documents.append({"name": name, "kind": kind, "size": info.get("size", 0)})
        return sorted(documents, key=lambda row: row["name"].casefold())

    def _cad_read_document(self, filename):
        company, folder = self._cad_context()
        try:
            kind = document_kind(filename, self.env.user.has_group("cad_link.group_cad_sources"))
        except ValueError as error:
            raise AccessError(_("Invalid CAD filename.")) from error
        if not kind:
            raise AccessError(_("This file type is not allowed for your CAD access group."))
        fs = self._cad_filesystem(company)
        path = posixpath.join(folder, filename)
        info = self._cad_info(fs, company, path)
        if info.get("type") != "file":
            raise AccessError(_("Not a regular CAD file."))
        limit = company.cad_max_file_mb * 1024 * 1024
        if info.get("size", 0) > limit:
            raise UserError(_("The file exceeds the configured CAD size limit."))
        with fs.open(path, "rb") as stream:
            data = stream.read(limit + 1)
        if len(data) > limit:
            raise UserError(_("The file exceeds the configured CAD size limit."))
        if kind == "pdf" and not data.startswith(b"%PDF-"):
            raise UserError(_("This file does not have a valid PDF signature."))
        return data, kind


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_open_cad_documents(self):
        self.ensure_one()
        if not self.env.user.has_group("cad_link.group_cad_documents"):
            raise AccessError(_("CAD document access is required."))
        self.check_access_rights("read")
        self.check_access_rule("read")
        variants = self.with_context(active_test=False).product_variant_ids
        if len(variants) == 1:
            return variants.action_open_cad_documents()
        return {
            "type": "ir.actions.act_window", "name": _("Select a CAD variant"),
            "res_model": "product.product", "view_mode": "tree,form",
            "domain": [("product_tmpl_id", "=", self.id)],
            "context": {"active_test": False, "create": False},
        }
