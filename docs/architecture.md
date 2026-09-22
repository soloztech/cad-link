# Architecture

```text
Odoo product / variant
  → CAD-link access and company checks
  → validated internal reference + configured relative directory
  → OCA fs_storage → fsspec → existing SMB share / local repository
```

`cad_link` extends `res.company`, `product.product` and `product.template`. It
does not create a parallel product catalog, document database or attachment store.
The source repository is read at the user's request. Form rendering does not
contact the file server.

- `paths.py`: pure validation and path construction, independently testable.
- `models/res_company.py`: configuration per company, administrative fields.
- `models/product.py`: access checks, variant resolution, listing and bounded reads.
- `controllers/documents.py`: authenticated listing and file delivery.
- `views/`: company configuration, product CAD tabs and an escaped QWeb listing.

Only internal private methods obtain the storage object using administrative
configuration. Product and company checks happen first. No public RPC method
accepts a storage ID or arbitrary filesystem path. Routes accept a product ID,
an authorized company ID and a validated single filename.

The service reads files with `rb`. It never creates or updates `ir.attachment`,
uses the storage's marker test, or changes FS Storage settings. Native formats
are sent as downloads; PDFs require a PDF signature and use the browser's viewer.
All document responses are private and non-cacheable. Filenames are escaped in
HTML and URLs. Provider exception details are not exposed to users.

Future CAD application connectors should publish exports to the existing
repository and expose an explicit interoperability contract. The Odoo addon
must remain usable without Autodesk software installed on the Odoo host.
