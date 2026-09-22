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
- `glb.py`: GLB container/resource validation, independently testable.
- `models/res_company.py`: configuration per company, administrative fields.
- `models/product.py`: access checks, variant resolution, listing and bounded reads.
- `controllers/documents.py`: authenticated listing, file delivery, 3D iframe and preview.
- `views/`: company configuration, product CAD tabs, listing and 3D iframe template.
- `static/src/`: inline OWL document list and the standalone 3D adapter.
- `static/lib/`: integrity-pinned local renderer with third-party notices.
- `desktop/windows/`: optional per-user Windows protocol handler, installer and tests.
- `desktop/inventor/`: optional iLogic GLB exporter, translator inspection and
  per-user configuration; runs inside the engineer's Inventor session.

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

The Windows client is optional. PDF/GLB browser viewing, the separate document route
and downloads continue to work without it. The protocol does not carry an Odoo
session and is not proof of authorization; the client's restrictions and SMB ACLs
apply independently.

## Browser 3D boundary

The inline list advertises **View 3D** for authorized GLB rows without reading
every model. Clicking creates a standalone iframe; closing/refreshing unmounts
it. The iframe uses the local `@google/model-viewer` 4.3.1 bundle and a separate
LGPL adapter, without a Website addon dependency. Vendor hashes and licenses
are recorded in [THIRD_PARTY.md](../THIRD_PARTY.md).

The iframe and `/preview/` endpoint repeat source-group, product and company
checks. The preview endpoint performs the existing bounded read, validates GLB
headers/chunks and embedded resources, then serves `model/gltf-binary` with
`private, no-store`. Each viewer instance uses a fresh URL to avoid renderer
caching after a GLB is replaced. Downloads use the original download endpoint.

The iframe's CSP restricts requests to the selected authenticated model endpoint
and blob resources; scripts/styles are local and remote workers are prohibited.
Embedded PNG/JPEG image blobs require `blob:` loading. The upstream bundle eagerly
initializes bundled WebAssembly, so this iframe permits `wasm-unsafe-eval` while
continuing to prohibit JavaScript `unsafe-eval`. URI-bearing resources and
unsupported extensions are rejected before the renderer receives the model.

The iframe intentionally permits same-origin scripts to use authenticated
requests. It is a separate rendering document, not an origin-isolation boundary
against arbitrary scripts; only fixed trusted templates/adapters are served.
The GLB validator, CSP, Odoo authorization and trusted repository writers remain
the relevant boundaries. Validation is not a complete glTF schema or GPU resource
budget check.

## Export on the CAD workstation

The optional Inventor rule publishes a GLB into the existing item folder after
an explicit manual setup or after-save event binding. It discovers the installed
translator, uses native export defaults and stages output in a temporary child
directory before replacing the top-level GLB. An export lock prevents overlapping
publication for that item. It does not save or change the native model.

The export companion and Windows URL launcher are separate programs. Neither
requires an Odoo password or service account credentials. Odoo needs no Autodesk
software or write access. A failed export keeps the previous GLB; operators must
inspect export status/logs rather than assume that an existing preview is current.
Parent assembly exports are not regenerated merely because a child part was saved.
See the [export contract and limitations](../desktop/inventor/README.md).
