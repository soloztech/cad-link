# SPDX-License-Identifier: LGPL-3.0-or-later
from pathlib import Path
import tempfile

from odoo.tests.common import new_test_user


class CadFixture:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temporary = tempfile.TemporaryDirectory(prefix="cad-link-test-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.folder = cls.root / "Items" / "000001"
        cls.folder.mkdir(parents=True)
        (cls.folder / "000001.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
        (cls.folder / "000001.ipt").write_bytes(b"synthetic CAD fixture; not an Inventor model")
        (cls.folder / "private.env").write_bytes(b"synthetic excluded fixture")
        cls.storage = cls.env["fs.storage"].create({
            "name": "CAD test storage", "code": "cad_link_test_storage", "protocol": "file",
            "directory_path": str(cls.root), "check_connection_method": "ls",
        })
        cls.company = cls.env.company
        cls.company.write({
            "cad_storage_id": cls.storage.id, "cad_items_directory": "Items",
            "cad_unc_root": r"\\fileserver\CAD$", "cad_max_file_mb": 1,
        })
        cls.product = cls.env["product.product"].create({
            "name": "Synthetic pillar", "default_code": "000001", "company_id": cls.company.id,
        })
        cls.reader = new_test_user(cls.env, login="cad_pdf_test", groups="cad_link.group_cad_documents")
        cls.engineer = new_test_user(cls.env, login="cad_source_test", groups="cad_link.group_cad_sources")
        cls.outsider = new_test_user(cls.env, login="cad_no_access_test", groups="base.group_user")

    def as_user(self, user):
        return self.product.with_user(user).with_context(allowed_company_ids=[self.company.id])
