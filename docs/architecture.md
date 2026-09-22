# Architecture

```text
Odoo product / variant
  → CAD-link access and company checks
  → validated internal reference + configured relative directory
  → OCA fs_storage → fsspec → existing SMB share / local repository
```

`cad_link` extends `res.company`, `product.product` and `product.template`. It
does not create a parallel product catalog, document database or attachment store.
The source repository is read when the CAD tab is mounted or the user refreshes
the listing. Other product tabs do not load the repository listing.

- `paths.py`: pure validation and path construction, independently testable.
- `models/res_company.py`: configuration per company, administrative fields.
- `models/product.py`: access checks, variant resolution, listing and bounded reads.
- `controllers/documents.py`: authenticated listing and file delivery.
- `views/`: company configuration, product CAD tabs and an escaped QWeb listing.
- `static/src/`: inline OWL document list and actions in the product form.
- `desktop/windows/`: optional per-user Windows protocol handler, installer and tests.

Only internal private methods obtain the storage object using administrative
configuration. Product and company checks happen first. No public RPC method
accepts a storage ID or arbitrary filesystem path. Routes accept a product ID,
an authorized company ID and a validated single filename.

The service reads files with `rb`. It never creates or updates `ir.attachment`,
uses the storage's marker test, or changes FS Storage settings. Native formats
are sent as downloads; PDFs require a PDF signature and use the browser's viewer.
All document responses are private and non-cacheable. Filenames are escaped in
HTML and URLs. Provider exception details are not exposed to users.

When explicitly enabled, the inline list includes `cad-link://open?path=...`
and `cad-link://folder?path=...` URLs generated from the configured UNC root and
authorized item/filename. The desktop client validates each request against its
own explicit UNC root and file-type allowlists before invoking Windows. An open
action uses the registered application; a folder action opens Explorer and selects
the file where applicable. No CAD content or service credentials are sent to the
client by this protocol. Odoo groups do not impersonate a Windows account or grant
network access. Native application edits use the user's existing file-server rights.

The Windows client is optional. PDF browser viewing, the separate document route
and downloads continue to work without it. The protocol does not carry an Odoo
session and is not proof of authorization; the client's restrictions and SMB ACLs
apply independently.

Future CAD application connectors should publish exports to the existing
repository and expose an explicit interoperability contract. The Odoo addon
must remain usable without Autodesk software installed on the Odoo host.
