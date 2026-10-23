"""Run pinned reference functions locally or as a trusted-LAN HTTP worker."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REFERENCE = Path(__file__).resolve().with_name('reference-cli.cjs')
MAX_BODY = 16 * 1024 * 1024
DECIMAL = re.compile(r'(?:0|[1-9][0-9]*)\Z')


def _strict_loads(raw):
    def invalid(value):
        raise ValueError(f'Nonfinite JSON value: {value}')
    return json.loads(raw, parse_constant=invalid)


def _reference(requests, node='node'):
    data = ''.join(json.dumps(item, allow_nan=False, separators=(',', ':')) + '\n' for item in requests)
    completed = subprocess.run(
        [node, str(REFERENCE)], input=data, text=True, capture_output=True,
        timeout=600, check=False,
    )
    if completed.returncode:
        raise RuntimeError(f'Reference process exited {completed.returncode}: {completed.stderr[:1000]}')
    if len(completed.stdout.encode('utf-8')) > MAX_BODY:
        raise ValueError('Reference result exceeds transport limit; use smaller task chunks')
    lines = completed.stdout.splitlines()
    if len(lines) != len(requests):
        raise RuntimeError('Reference returned a different number of protocol responses')
    results = []
    for line in lines:
        response = _strict_loads(line)
        if not isinstance(response, dict) or response.get('ok') is not True:
            raise RuntimeError(f'Reference rejected request: {response.get("error") if isinstance(response, dict) else response}')
        results.append(response['result'])
    return results


def describe_manifest(manifest, node='node'):
    return _reference([{'op': 'describe', 'manifest': manifest}], node)[0]


def execute_lease(lease, node='node'):
    """Execute one bounded lease, without opening or writing the coordinator DB."""
    if not isinstance(lease, dict):
        raise ValueError('Lease must be an object')
    for field in ('start', 'end'):
        if not isinstance(lease.get(field), str) or not DECIMAL.fullmatch(lease[field]):
            raise ValueError(f'Invalid {field} ordinal')
    start, end = int(lease['start']), int(lease['end'])
    if not 1 <= end - start <= 32:
        raise ValueError('A lease must contain 1..32 trials')
    manifest = lease.get('manifest')
    if not isinstance(manifest, dict):
        raise ValueError('Missing manifest')
    if not isinstance(lease.get('solver_digest'), str) or not re.fullmatch(r'[0-9a-f]{64}', lease['solver_digest']):
        raise ValueError('Lease must pin a solver digest')
    results = _reference([
        {'op': 'simulate', 'manifest': manifest, 'ordinal': str(i), 'replay': True}
        for i in range(start, end)
    ], node)
    for ordinal, result in zip(range(start, end), results):
        if (result.get('ordinal') != str(ordinal)
                or result.get('experiment_id') != lease.get('experiment_id')
                or result.get('solver_digest') != lease['solver_digest']
                or result.get('trial_id') != f"{lease.get('experiment_id')}:{ordinal}"):
            raise RuntimeError('Reference result identity does not match its lease')
    return results


def _post(url, route, payload):
    data = json.dumps(payload, allow_nan=False, separators=(',', ':')).encode()
    if len(data) > MAX_BODY:
        raise ValueError('Submission exceeds 16 MiB; reduce chunk size')
    req = urllib.request.Request(url + route, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read(MAX_BODY + 1)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'Coordinator returned HTTP {exc.code}: {exc.read(2000).decode(errors="replace")}') from exc
    if len(raw) > MAX_BODY:
        raise ValueError('Coordinator response exceeds transport limit')
    return _strict_loads(raw)


def remote_worker(url, worker_id, node='node', once=False):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.query or parsed.fragment or parsed.username:
        raise ValueError('Use an HTTP(S) coordinator origin without credentials, query or fragment')
    if parsed.path not in ('', '/'):
        raise ValueError('Coordinator URL must be an origin without a path')
    if not isinstance(worker_id, str) or not worker_id.strip() or len(worker_id) > 128:
        raise ValueError('Worker ID must be a nonempty string of at most 128 characters')
    url = url.rstrip('/')
    accepted = 0
    while True:
        response = _post(url, '/v1/lease', {'worker_id': worker_id})
        lease = response.get('lease')
        if lease is None:
            return accepted
        identity = {'task_id': lease['task_id'], 'worker_id': worker_id, 'epoch': lease['epoch']}
        stopped = threading.Event()
        heartbeat_errors = []

        def heartbeat():
            while not stopped.wait(10):
                try:
                    _post(url, '/v1/heartbeat', identity)
                except Exception as exc:
                    heartbeat_errors.append(exc)
                    return

        thread = threading.Thread(target=heartbeat, name='lease-heartbeat', daemon=True)
        thread.start()
        try:
            results = execute_lease(lease, node)
            if heartbeat_errors:
                raise RuntimeError(f'Lease heartbeat failed: {heartbeat_errors[0]}')
            # Stop heartbeat before publication; after commit the lease is complete.
            stopped.set()
            thread.join(timeout=31)
            if thread.is_alive() or heartbeat_errors:
                raise RuntimeError('Lease could not be renewed safely')
            submitted = _post(url, '/v1/results', {**identity, 'results': results})
            accepted += submitted['accepted']
            print(json.dumps({'task_id': lease['task_id'], **submitted}), flush=True)
        finally:
            stopped.set()
            thread.join(timeout=31)
        if once:
            return accepted


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--worker-id', required=True)
    parser.add_argument('--node', default='node')
    parser.add_argument('--once', action='store_true', help='Execute at most one available lease')
    args = parser.parse_args(argv)
    try:
        count = remote_worker(args.url, args.worker_id, args.node, args.once)
        print(json.dumps({'worker_id': args.worker_id, 'accepted': count}))
        return 0
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as exc:
        print(f'Worker failed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
