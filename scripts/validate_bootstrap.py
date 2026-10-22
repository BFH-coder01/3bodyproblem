"""Check the tracked bootstrap inventory and task dependencies without dependencies."""
from pathlib import Path
import hashlib
import json


def validate(root):
    manifest = json.loads((root / 'PACK_MANIFEST.json').read_text())
    for name, expected in manifest['files_sha256'].items():
        path = root / name
        assert path.resolve().is_relative_to(root.resolve()), name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
    tasks = {}
    for path in sorted((root / 'ops/tasks').glob('*.json')):
        task = json.loads(path.read_text())
        assert task['task_id'] not in tasks, path
        tasks[task['task_id']] = task
    visited, active = set(), set()

    def visit(key):
        assert key in tasks, f'Unknown dependency: {key}'
        assert key not in active, f'Dependency cycle at {key}'
        if key in visited:
            return
        active.add(key)
        for dep in tasks[key]['dependencies']:
            visit(dep)
        active.remove(key)
        visited.add(key)

    for key in tasks:
        visit(key)
    json.loads((root / 'configs/experiment-point-close-stop.example.json').read_text())
    print(f"PASS: {len(manifest['files_sha256'])} file hashes, {len(tasks)} task manifests, acyclic dependencies and experiment JSON")


if __name__ == '__main__':
    validate(Path(__file__).resolve().parents[1])
