"""Build the isolated C++17 FP64 reference with a local GNU-compatible compiler."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ('native/include/threebody.hpp', 'native/core/threebody.cpp', 'native/cli/main.cpp')
FLAGS = ('-std=c++17', '-O2', '-fno-fast-math', '-ffp-contract=off', '-Wall', '-Wextra', '-Wpedantic')


def build(output, cxx='c++'):
    """Return recorded build identity; never install a toolchain or invoke a shell."""
    compiler = shutil.which(cxx)
    if compiler is None:
        raise RuntimeError(f'C++ compiler not found: {cxx}')
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    source_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}
    version = subprocess.run([compiler, '--version'], text=True, capture_output=True,
                             timeout=15, check=True).stdout.splitlines()
    version = version[0] if version else 'Compiler returned no version text'
    descriptor = json.dumps({'sources': source_hashes, 'flags': FLAGS, 'compiler': version},
                            sort_keys=True, separators=(',', ':')).encode()
    build_id = hashlib.sha256(descriptor).hexdigest()
    handle, temporary = tempfile.mkstemp(prefix=output.name + '.', suffix='.tmp', dir=output.parent)
    os.close(handle)
    try:
        command = [compiler, *FLAGS, '-I', str(ROOT / 'native/include'),
                   str(ROOT / 'native/core/threebody.cpp'), str(ROOT / 'native/cli/main.cpp'),
                   '-o', temporary]
        completed = subprocess.run(command, text=True, capture_output=True, timeout=120)
        if completed.returncode:
            raise RuntimeError(f'Native compile failed ({completed.returncode}): {completed.stderr[-8000:]}')
        if os.name != 'nt':
            os.chmod(temporary, 0o755)
        binary_hash = hashlib.sha256(Path(temporary).read_bytes()).hexdigest()
        metadata = {'format': 'threebody.native-build.v1', 'build_id': build_id,
                    'compiler': version, 'compiler_path': compiler, 'flags': list(FLAGS),
                    'precision': 'fp64', 'fast_math': False, 'sources_sha256': source_hashes,
                    'binary_sha256': binary_hash, 'binary': str(output),
                    'compile_stdout': completed.stdout[-4000:], 'compile_stderr': completed.stderr[-4000:]}
        os.replace(temporary, output)
        sidecar = output.with_name(output.name + '.build.json')
        with tempfile.NamedTemporaryFile(mode='w', dir=sidecar.parent, delete=False, encoding='utf-8') as stream:
            json.dump(metadata, stream, indent=2)
            stream.write('\n')
            metadata_path = stream.name
        try:
            os.replace(metadata_path, sidecar)
        finally:
            Path(metadata_path).unlink(missing_ok=True)
        return metadata
    finally:
        Path(temporary).unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default=str(ROOT / 'build/native-reference'))
    parser.add_argument('--cxx', default='c++', help='Local GNU-compatible C++17 compiler executable')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(build(args.out, args.cxx), allow_nan=False))
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
