# Alpha validation — 2026-09-22

## Inline CAD tab and Windows launcher (16.0.1.1.0)

- Updated Odoo ORM/HTTP suite: **33 tests passed, zero failures and zero errors**
  in an isolated database with synthetic products and documents.
- **5 standalone Python tests passed**; Python, XML, manifest asset paths and
  JavaScript syntax were checked.
- Windows PowerShell 5.1 launcher suite: **71 checks passed**, including URI/query
  validation, root boundaries, traversal, file types and simulated reparse points.
- Windows executable compilation and noninteractive rejection smoke passed.
- The launcher accepts the single slash Windows inserts before the query when
  dispatching a custom URL; other unexpected path segments remain rejected.
- An isolated upgrade from 16.0.1.0.1 to 16.0.1.1.0 passed the same 33 Odoo tests;
  the new stored company setting remained disabled by default for existing companies.
- Odoo tests cover role-filtered inline rows, retained download links, PDF preview
  links, optional desktop links, UNC encoding, variants and sanitized provider errors.

These checks do not validate every CAD application's file associations or project
configuration. Direct opening needs a Windows acceptance test against the intended
share and associated application. Browser prompts and corporate protocol policies
also depend on each workstation.

## Initial alpha

Executed in an isolated Odoo 16/OCB environment with a disposable PostgreSQL
database and synthetic products, users and files. OCA `fs_storage` came from
commit `15c2abdee2533b48d74a8bf8cb24a710013d9445` of its `16.0` branch;
fsspec version 2026.9.0.

- Standalone path/extension suite: **5 tests passed**, with multiple invalid-path cases.
- Odoo ORM and HTTP suite: **20 tests passed, zero failures and zero errors**.
- Python syntax, XML syntax and manifest data paths validated.
- A clean install and a subsequent module update were exercised.

The Odoo suite covers PDF-only/source access, direct URL denial, configuration
privacy, product record rules, company boundaries, leading zeros, duplicate and
archived codes, case-insensitive matches, literal underscores, missing folders,
path traversal, local symlinks, file size, PDF signatures and variant selection.

The first test run exposed two incorrect duplicate-code fixtures: Odoo's variant
copy operation delegates to template copying. The fixtures now explicitly create
the intended variants and verify their references. The final suite passed.

File I/O tests use a local filesystem backend and synthetic content. The HTTP
suite verifies responses and permission behavior; it is not a visual browser
review or validation of a real Inventor assembly. SMB behavior across different
file servers and an installation's complete permission model still require
environment-specific acceptance testing before production deployment.

No production deployment is included in this validation or implied by a commit.
