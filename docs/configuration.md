# Configuration

## Storage and folders

Use an existing OCA `fs.storage` record, protocol `smb` or `file`. This alpha
does not claim support for every backend exposed by fsspec. Start with a small
test repository and read-only service credentials.

For an SMB share `\\fileserver\CAD$`, the FS Storage directory can be `/CAD$`.
Example options, with environment references resolved by FS Storage:

```json
{
  "host": "fileserver",
  "port": 445,
  "username": "$CAD_SMB_USERNAME",
  "password": "$CAD_SMB_PASSWORD",
  "encrypt": true,
  "timeout": 10,
  "register_session_retries": 0,
  "share_access": "rwd",
  "auto_mkdir": false
}
```

Enable **Resolve env vars** and use the **List directory** connection test.
Supply the variables to your Odoo service using your normal secret-management
mechanism. Do not paste credentials into this repository or issue reports.
`share_access: rwd` controls file-handle sharing with CAD applications; it does
not grant write permission to the service account. Enforce read access on the server.

Company settings:

| Field | Example | Meaning |
|---|---|---|
| CAD storage | Engineering repository | Existing FS Storage record |
| Items directory | `Items` | Relative to the configured storage root; may be empty |
| Windows share | `\\fileserver\CAD$` | Optional UNC equivalent of that root |
| Maximum file size | `50` MiB | Per-request read limit, configurable from 1 to 256 MiB |
| Enable CAD-link Desktop | Off by default | Show direct network/Explorer actions; requires the optional Windows client |

Use one folder per variant's **Internal Reference** (`product.product.default_code`).
Codes remain strings, including leading zeros. Missing, ambiguous or duplicate
references fail with an explicit error instead of picking another product.
Duplicates are checked across global products and products in the selected company,
including archived records and case-insensitive matches for Windows compatibility.
Global products resolve against the active company selected when opening CAD.

## Inline list and opening originals

Open the product's **CAD** tab to list the authorized files, then use **Refresh**
after new exports are saved to the repository. PDF files provide **View PDF**;
every permitted file retains **Download**. Unsaved product changes must be saved
before reloading the list so paths resolve from the saved internal reference.

To add **Open on network**, **Show in folder**, and **Open item folder**, install
the [optional Windows client](../desktop/windows/README.md) under each intended
Windows user with explicit allowed UNC roots. Configure the matching Windows
share above, then enable CAD-link Desktop. The browser may ask permission to
invoke the registered `cad-link` protocol. It cannot reliably detect whether the
client or the appropriate CAD application is installed. Keep the copyable path
available as a fallback.

Network open invokes the application associated with the extension on that
workstation. It does not install Inventor, change associations, copy assembly
dependencies or create a local download. Opening a shared original is subject
to the CAD application's file locks and existing references. Download remains
a separate action that copies one file.

The first alpha lists direct children only. Put exported PDFs next to the source
files. Nested exports, revisions and alternate path templates are future work.
No folder is created automatically. A missing folder and an empty folder are
different states. Listings are capped at 500 entries.

## Access

- **PDF documents**: list, view and download `.pdf` files.
- **PDF and CAD sources**: PDFs plus `.ipt`, `.iam`, `.idw`, `.dwg`, `.dxf`,
  `.step`, `.stp`, `.iges`, `.igs`, `.sat`, `.stl`, `.obj`, `.mtl`, `.glb`, `.gltf`.
- Both require an internal Odoo user and existing read access to the product.
- Administrative configuration does not automatically grant CAD document access.
- Configuration fields and FS Storage credentials remain administrative.

Every HTTP file request rechecks group membership, product access and company
membership, even if the URL was obtained from someone else. Portal/public users
are not supported. A PDF-only user cannot bypass the native-file restriction
by guessing a direct URL.

SMB/NTFS permissions govern direct access through Explorer and the service account;
Odoo groups govern requests made through Odoo. The Odoo account does not impersonate
each Windows user. Browser PDF viewing is not a mechanism for preventing downloads.

## Operational limits

- Original CAD files require a compatible CAD application. Browser PDF preview
  requires an existing, valid PDF; CAD-link does not generate exports.
- Downloads contain a single file. Assemblies may require other referenced files;
  this release does not package dependencies or provide checkout/locking.
- No writes, markers, attachment copies, background crawl or approval workflow.
- Files are buffered in memory up to the configured size limit; size the limit
  for worker memory and concurrency. Byte-range streaming is not implemented.
- Engineering authors must be trusted. Symbolic links/reparse points are unsupported;
  do not place them in a configured repository. Path validation is not a replacement
  for storage ACLs or an atomic checkout. Concurrent edits can affect a read.
- Existing native filesystem libraries and Odoo remain responsible for transport,
  storage configuration, dependency updates and operational backups.
