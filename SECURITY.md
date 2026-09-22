# Security

This project is an alpha. Supported development currently targets the `16.0`
branch; no stable release or security support period has been declared.

Report vulnerabilities using this repository's **Security → Report a vulnerability**
private reporting feature. Include a minimal synthetic reproduction, affected
commit, Odoo version and storage protocol. Do not include credentials, real
engineering documents or customer details.

The optional Windows client registers a per-user `cad-link` URL handler. Install
it only from reviewed source and configure explicit UNC roots. The handler rejects
arbitrary local paths, traversal and unsupported file types; it does not receive
or enforce Odoo authentication. Any local application or website can attempt to
invoke a registered protocol. Windows/file-server ACLs and the configured roots
remain independent requirements. Opening a permitted CAD/PDF invokes its installed
application, whose own handling of documents and active content still applies.

Deploy with read-only service credentials and explicit Odoo groups. Restrict
direct file access independently using server ACLs. Only trusted authors should
write to the repository; symlinks and reparse points are unsupported.

Consult the configuration guide for file-size, concurrent-edit and download
limitations. Dependencies, the Odoo host and the file server require their own
security maintenance.
