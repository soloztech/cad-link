# Third-party software

CAD-link's original code is LGPL-3.0-or-later. The isolated 3D viewer includes
unmodified **@google/model-viewer 4.3.1**, distributed under Apache-2.0, with its
bundled dependencies under the licenses listed in
[THIRD_PARTY_NOTICES.txt](cad_link/static/lib/model-viewer/4.3.1/THIRD_PARTY_NOTICES.txt).

- [Upstream source and release](https://github.com/google/model-viewer/releases/tag/v4.3.1)
- [Apache license](cad_link/static/lib/model-viewer/4.3.1/LICENSE)
- [Pinned archive integrity and file hashes](cad_link/static/lib/model-viewer/4.3.1/provenance.json)

The renderer is served locally. CAD-link does not load CDN scripts or remote
texture/decoder resources. The CAD-link adapter was written independently and
does not depend on any website addon.

Run `python3 tools/vendor_model_viewer.py` to verify the checked-in files and
`python3 tools/vendor_model_viewer.py --upstream` to additionally compare the
renderer/license against the integrity-pinned upstream npm archive.
