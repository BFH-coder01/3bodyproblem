"""Refresh the SHA-256 inventory after staging all intended source files."""
from pathlib import Path
import hashlib
import json
import subprocess


def tracked_hashes(root):
    files = subprocess.run(['git', 'ls-files', '-z'], cwd=root, check=True,
                           capture_output=True).stdout.decode().split('\0')
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in sorted(files) if name and name != 'PACK_MANIFEST.json'}


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'PACK_MANIFEST.json').read_text())
    manifest['format'] = 'three-body-source-inventory-v1'
    manifest['files_sha256'] = tracked_hashes(root)
    (root / 'PACK_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f"Updated {len(manifest['files_sha256'])} tracked file hashes")
