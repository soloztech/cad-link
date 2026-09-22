# CAD-link

Shared CAD documents, accessible from Odoo products.

[Português](docs/README.pt-BR.md) · [Setup](docs/configuration.md) · [Architecture](docs/architecture.md) · [Roadmap](docs/roadmap.md)

**Alpha · Odoo 16 · 16.0.1.2.0 · LGPL-3.0-or-later**

CAD-link connects a product variant's internal reference to a folder in an existing
engineering repository. Engineers keep using their CAD tools and file explorer;
Odoo users can consult the documents their access group permits. Files stay in
the shared repository.

```text
Product reference       Shared repository
P-2200              →   Items/P-2200/
                         P-2200.ipt
                         P-2200.pdf
                         P-2200.glb
```

## Included in this alpha

- Company-specific storage configuration using OCA `fs_storage`.
- A CAD tab on product and variant forms. Multiple variants require selecting
  the variant; a template is never assumed to have one shared item code.
- File listing inside the CAD tab, loaded when the tab opens, with a refresh action.
- Authenticated PDF viewing through the browser and file downloads.
- On-demand GLB 3D viewing inside the CAD tab, with rotation, zoom, reset and
  full screen. The locally bundled renderer displays embedded PNG/JPEG textures.
- Optional Windows desktop client to open originals on the network or show them
  in Explorer; downloads remain available alongside these actions.
- Separate access groups for PDF documents and CAD source files.
- An optional UNC path that users can copy into Windows Explorer.
- Internal reference validation, duplicate detection (including archived and
  case-insensitive matches), product access rules and company checks.
- Read-only Odoo operations: no upload, rename, migration or attachment duplication.
- An optional [Inventor iLogic export companion](desktop/inventor/README.md),
  configurable for publishing GLBs after saving a part or assembly. A real export
  and after-save event require a pilot on the intended workstation.

This release supports SMB and local filesystem backends. The browser previews
existing GLB exports; it does not parse native Inventor files. Odoo does not run
CAD conversion, generate PDFs, synchronize BOMs or impose a drawing approval
workflow. Export runs in the optional Inventor companion, with the engineer's
Windows permissions. Network actions and **Download** remain available.

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

For browser 3D, place a self-contained GLB 2.0 beside the native file and select
**Refresh → View 3D**. The **PDF and CAD sources** group is required; the PDF-only
group does not gain access to 3D geometry. The default read limit is 50 MiB per
file. Export embedded PNG/JPEG textures without compression or external resource
URIs. Inventor and the Windows launcher are unnecessary on a viewing workstation.
See [3D configuration](docs/configuration.md#3d-preview) and the
[Inventor export setup](desktop/inventor/README.md) for automatic publishing.

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
python3 tools/vendor_model_viewer.py
```

Run the Odoo integration and HTTP tests in a disposable database with the
dependencies on `addons_path`:

```bash
odoo -c /path/to/test.conf -d cad_link_test -i cad_link \
  --test-enable --test-tags /cad_link --stop-after-init --without-demo=all
```

These tests create synthetic products, users and temporary files. Never target
a production database. GitHub Actions runs the standalone path/GLB tests and static
checks; the Odoo suite is a separate integration check.
See the [validation record](docs/validation.md) for the tested scope and remaining
Inventor pilot requirements.

## Community

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md),
[SECURITY.md](SECURITY.md) and the [roadmap](docs/roadmap.md).
The project is independent of Autodesk and the Odoo Community Association.
OCA `fs_storage` remains an external dependency with its own authorship.

Original code is licensed under [LGPL-3.0-or-later](LICENSE); renderer licenses and
attributions are listed in [THIRD_PARTY.md](THIRD_PARTY.md). The underlying GPL terms are
included in [COPYING](COPYING). Copyright 2026 CAD-link contributors.
