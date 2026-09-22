# Initial alpha validation — 2026-09-22

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
