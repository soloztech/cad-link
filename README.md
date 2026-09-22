# CAD-link

Shared CAD documents, accessible from Odoo products.

[Português](docs/README.pt-BR.md) · [Setup](docs/configuration.md) · [Architecture](docs/architecture.md) · [Roadmap](docs/roadmap.md)

**Alpha · Odoo 16 · LGPL-3.0-or-later**

CAD-link connects a product variant's internal reference to a folder in an existing
engineering repository. Engineers keep using their CAD tools and file explorer;
Odoo users can consult the documents their access group permits. Files stay in
the shared repository.

```text
Product reference       Shared repository
P-2200              →   Items/P-2200/
                         P-2200.ipt
                         P-2200.pdf
```

## Included in this alpha

- Company-specific storage configuration using OCA `fs_storage`.
- A CAD tab on product and variant forms. Multiple variants require selecting
  the variant; a template is never assumed to have one shared item code.
- File listing inside the CAD tab, loaded when the tab opens, with a refresh action.
- Authenticated PDF viewing through the browser and file downloads.
- Optional Windows desktop client to open originals on the network or show them
  in Explorer; downloads remain available alongside these actions.
- Separate access groups for PDF documents and CAD source files.
- An optional UNC path that users can copy into Windows Explorer.
- Internal reference validation, duplicate detection (including archived and
  case-insensitive matches), product access rules and company checks.
- Read-only operations: no upload, rename, migration or attachment duplication.

This release supports SMB and local filesystem backends. It does not render
Inventor files, generate PDFs, convert CAD to GLB, synchronize BOMs or impose a
drawing approval workflow. GLB and other allowed source files can be downloaded;
an embedded 3D viewer is a future milestone.

## Quick start

1. Install Odoo 16 and [OCA `fs_storage`](https://github.com/OCA/storage/tree/16.0/fs_storage).
   Install `fsspec` and the protocol dependencies in the Python environment that
   actually runs Odoo. SMB requires `smbprotocol`.
2. Clone the `16.0` branch and add the repository root to Odoo's `addons_path`.
3. Install `cad_link` in a test database first.
4. Configure an FS Storage backend with **read-only credentials** and connection
   test **List directory**, then select it on **Settings → Users & Companies →
   Companies → CAD-link**. Company settings require administrative access.
5. Grant a CAD-link group to an internal user who already has product access.
6. Set a unique internal reference on a product variant, create its folder through
   your engineering process, and open the **CAD** tab.

For direct network opening, install the optional [Windows desktop client](desktop/windows/README.md)
on each workstation, explicitly allow the repository's UNC root, then enable
**CAD-link Desktop** in the company configuration. A compatible CAD application
and the Windows user's own network permissions are required. The client opens
the shared original; **Download** still creates a separate local copy.

Configuration is deliberately empty at installation. No service accounts,
network mappings, production endpoints or user permissions are provisioned.
See the [configuration guide](docs/configuration.md) for directory and permission details.

```bash
git clone --branch 16.0 https://github.com/soloztech/cad-link.git
```

## Development

```bash
python3 tools/check_repository.py
python3 -m unittest discover -s tests -v
```

Run the Odoo integration and HTTP tests in a disposable database with the
dependencies on `addons_path`:

```bash
odoo -c /path/to/test.conf -d cad_link_test -i cad_link \
  --test-enable --test-tags /cad_link --stop-after-init --without-demo=all
```

These tests create synthetic products, users and temporary files. Never target
a production database. GitHub Actions runs the standalone path tests and static
checks; the Odoo suite is a separate integration check.
See the [initial validation record](docs/validation.md) for the tested scope.

## Community

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md),
[SECURITY.md](SECURITY.md) and the [roadmap](docs/roadmap.md).
The project is independent of Autodesk and the Odoo Community Association.
OCA `fs_storage` remains an external dependency with its own authorship.

Code is licensed under [LGPL-3.0-or-later](LICENSE); the underlying GPL terms are
included in [COPYING](COPYING). Copyright 2026 CAD-link contributors.
