# SPDX-License-Identifier: LGPL-3.0-or-later
"""Verify the vendored renderer; never install a moving latest package."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", action="store_true", help="Also verify against the pinned npm archive")
    args = parser.parse_args()
    directory = Path(__file__).resolve().parents[1] / "cad_link/static/lib/model-viewer/4.3.1"
    provenance = json.loads((directory / "provenance.json").read_text())
    for name, expected in provenance["files"].items():
        data = (directory / name).read_bytes()
        if len(data) != expected["bytes"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
            raise SystemExit("Vendored file integrity mismatch: " + name)
    if args.upstream:
        with urllib.request.urlopen(provenance["tarball"], timeout=60) as response:
            archive = response.read(10 * 1024 * 1024 + 1)
        integrity = "sha512-" + base64.b64encode(hashlib.sha512(archive).digest()).decode()
        if integrity != provenance["npm_integrity"]:
            raise SystemExit("Pinned upstream archive integrity mismatch")
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
            for name, member in (("model-viewer.min.js", "package/dist/model-viewer.min.js"), ("LICENSE", "package/LICENSE")):
                if tar.extractfile(member).read() != (directory / name).read_bytes():
                    raise SystemExit("Upstream file mismatch: " + name)
    print("model-viewer 4.3.1 integrity verified" + (" against upstream npm archive" if args.upstream else ""))


if __name__ == "__main__":
    main()
