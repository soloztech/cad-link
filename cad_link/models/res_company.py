# SPDX-License-Identifier: LGPL-3.0-or-later
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..paths import relative_directory, unc_directory


class ResCompany(models.Model):
    _inherit = "res.company"

    cad_storage_id = fields.Many2one(
        "fs.storage", string="CAD storage", groups="base.group_system",
        ondelete="restrict", help="Existing OCA FS Storage backend. Use read-only credentials.",
    )
    cad_items_directory = fields.Char(
        string="Items directory", default="Items", groups="base.group_system",
        help="Relative to the storage root. Leave empty if item folders are at the root.",
    )
    cad_unc_root = fields.Char(
        string="Windows share", groups="base.group_system",
        help="Optional UNC equivalent of the storage root; used by Explorer and CAD-link Desktop.",
    )
    cad_desktop_enabled = fields.Boolean(
        string="Enable CAD-link Desktop", groups="base.group_system", default=False,
        help="Show actions that open the original shared files on Windows. Requires the optional "
             "CAD-link Desktop client and a configured Windows share. Windows permissions still apply.",
    )
    cad_max_file_mb = fields.Integer(
        string="Maximum file size (MiB)", default=50, groups="base.group_system",
    )

    @api.constrains("cad_items_directory", "cad_unc_root", "cad_max_file_mb", "cad_storage_id", "cad_desktop_enabled")
    def _check_cad_configuration(self):
        for company in self:
            try:
                relative_directory(company.cad_items_directory or "")
                unc_directory(company.cad_unc_root or "", "")
            except ValueError as error:
                raise ValidationError(_("Invalid CAD directory: %s") % str(error)) from error
            if not 1 <= company.cad_max_file_mb <= 256:
                raise ValidationError(_("CAD file size must be between 1 and 256 MiB."))
            if company.cad_desktop_enabled and not company.cad_unc_root:
                raise ValidationError(_("Configure a Windows share before enabling CAD-link Desktop."))
            if company.cad_storage_id and company.cad_storage_id.protocol not in ("smb", "file"):
                raise ValidationError(_("This release supports SMB and local filesystem storage."))
