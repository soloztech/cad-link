# CAD-link contributor instructions

- This is a generic community project. Keep customer infrastructure, credentials,
  actual CAD documents and environment-specific defaults out of tracked files.
- `16.0` is the development branch for Odoo 16. The addon is `cad_link`.
- Use LGPL-3.0-or-later for original code and preserve third-party notices.
- Keep product/variant, Odoo access-group and company checks before storage access.
- Use read-only file operations. New write behavior requires an explicit design.
- Run standalone tests and syntax checks. Run Odoo ORM/HTTP tests for behavior changes.
- Use synthetic files and disposable databases. Do not run tests against production.
- Keep README capabilities and roadmap accurate. Do not describe proposed viewers,
  connectors, translations or versions as implemented.
- Do not deploy or publish a stable release merely because code was pushed.
