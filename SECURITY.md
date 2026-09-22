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

The browser 3D preview requires the **PDF and CAD sources** group, product read
access and the selected company. The PDF-only group cannot access GLBs through
the preview or download endpoints. Previewing a model delivers its geometry to
the browser; it is not a way to prevent users from obtaining that geometry.

Only self-contained GLB 2.0 resources are accepted for preview. Embedded PNG/JPEG
images are supported; resource URIs, unknown extensions and compressed formats
that would need additional decoders are rejected. Reads are bounded by the company
limit (50 MiB by default) and JSON is capped at 4 MiB. These checks enforce the
resource boundary, not the complete glTF schema or a maximum GPU/texture memory
budget. Repository authors must remain trusted.

The locally bundled renderer runs in a separate same-origin iframe with an
explicit CSP, without backend assets or external services. The CSP permits only
the selected model endpoint and image blobs for resource fetching. It allows
bundled WebAssembly via `wasm-unsafe-eval`, but does not enable JavaScript
`unsafe-eval` or remote workers. The iframe's same-origin script permission means
its sandbox is not an isolation boundary for arbitrary scripts: only the fixed
trusted template and adapter are served. Keep the renderer's
[third-party files and notices](THIRD_PARTY.md) intact when updating it.

The optional Inventor iLogic rules are executable code running with the engineer's
Windows permissions. Restrict modification of shared rule directories and global
event bindings to maintainers. Configure the item root explicitly and validate
manual exports before enabling after-save events. This companion writes GLBs;
the Odoo service should keep read-only rights. The export lock coordinates derived
file publication, not native CAD editing or parent assembly freshness. Failed
exports can leave an older GLB available; inspect the local exporter status/log.

Consult the configuration guide for file-size, concurrent-edit and download
limitations. Dependencies, the Odoo host and the file server require their own
security maintenance.
