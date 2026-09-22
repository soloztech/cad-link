# Roadmap

## Alpha: shared repository consultation

- [x] Company-specific OCA FS Storage configuration.
- [x] Product variant reference → item folder.
- [x] Direct-child listing, PDF browser preview and permitted downloads.
- [x] PDF / source groups, company boundaries and product access checks.
- [x] UNC copy field, path validation and bounded reads.
- [x] Standalone tests and Odoo ORM / HTTP tests.
- [x] Inline CAD tab listing with PDF viewing and retained download actions.
- [x] Optional Windows client to open shared originals and show files in Explorer.
- [x] Embedded, authenticated preview of self-contained GLB exports with locally
  bundled rendering and embedded PNG/JPEG textures.
- [x] Optional Inventor iLogic inspection/export rules with per-user configuration
  and documented after-save setup.
- [ ] Complete a real Inventor part/assembly export and after-save pilot on the
  intended workstation and SMB server, including material/scale checks.
- [ ] Validate with different organizations and SMB server implementations.
- [ ] Complete interface translations and publish a tagged release.

## Next increments

- Configurable PDF/export subdirectories and explicit revision handling.
- A portable export contract: source reference, revision, units, files and checksums.
- A dependency queue to regenerate parent assembly previews after component changes.
- An installer that preserves existing shared iLogic event bindings while adding
  the two CAD-link bindings.
- Inventor PDF export and property exchange beyond the current GLB companion.
- Optional connectors for other CAD applications.
- Efficient streaming for large files and assembly dependency packages.
- Additional Odoo versions and storage protocols, with dedicated integration tests.

There is no planned mandatory drawing approval workflow. BOM synchronization,
CAD editing and PDM replacement are not implied by the initial repository integration.
Unchecked items and next increments are proposals, not available features or
delivery commitments. An implemented companion is not evidence that it has been
enabled or validated on a particular Inventor workstation.
