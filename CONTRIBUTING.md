# Contributing

Use the `16.0` branch for Odoo 16 work. Open a focused pull request that explains
the problem, resulting behavior and validation. Keep all installation-specific
servers, paths, accounts and document samples out of the repository.

Code and UI strings are written in English; translations and documentation in
other languages are welcome. New code uses LGPL-3.0-or-later. Preserve authorship
and license notices when using third-party work.

Before submitting:

```bash
python3 tools/check_repository.py
python3 -m unittest discover -s tests -v
```

For changes to Odoo behavior, also run the module's ORM and HTTP tests in a
disposable Odoo 16 database; see the README command. Include a meaningful
regression test for access boundaries, variant resolution or file handling.
Use synthetic fixtures; do not commit native customer CAD files or credentials.

A pull request or merge does not authorize deployment to anyone's production
environment. Report vulnerabilities through private reporting rather than a
public issue containing sensitive reproduction details.
