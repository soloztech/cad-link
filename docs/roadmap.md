# Roadmap

## Alpha: shared repository consultation

- [x] Company-specific OCA FS Storage configuration.
- [x] Product variant reference → item folder.
- [x] Direct-child listing, PDF browser preview and permitted downloads.
- [x] PDF / source groups, company boundaries and product access checks.
- [x] UNC copy field, path validation and bounded reads.
- [x] Standalone tests and Odoo ORM / HTTP tests.
- [ ] Validate with different organizations and SMB server implementations.
- [ ] Complete interface translations and publish a tagged release.

## Next increments

- Configurable PDF/export subdirectories and explicit revision handling.
- Embedded 3D preview of generated GLB files, with documented material requirements.
- A portable export contract: source reference, revision, units, files and checksums.
- Optional Inventor connector to generate PDF/GLB exports and exchange properties.
- Optional connectors for other CAD applications.
- Efficient streaming for large files and assembly dependency packages.
- Additional Odoo versions and storage protocols, with dedicated integration tests.

There is no planned mandatory drawing approval workflow. BOM synchronization,
CAD editing and PDM replacement are not implied by the initial repository integration.
Roadmap items are proposals, not available features or delivery commitments.
