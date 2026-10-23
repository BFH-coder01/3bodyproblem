"""CPU pipeline CLI and trusted-local-network coordinator HTTP API."""
from __future__ import annotations
import argparse
import concurrent.futures
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import sys
import time
from urllib.parse import parse_qs, unquote, urlsplit

from .ledger import Ledger, LedgerError, dumps, integer

MAX_BODY = 16 * 1024 * 1024
ROOT = Path(__file__).resolve().parents[1]


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON field')
            result[key] = value
        return result

    def constant(_):
        raise ValueError('Nonfinite JSON number')

    try:
        parsed = json.loads(data, object_pairs_hook=pairs, parse_constant=constant)
        dumps(parsed)
        return parsed
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise LedgerError('Invalid finite JSON document') from exc


def fields(body, expected):
    if not isinstance(body, dict) or set(body) != set(expected):
        raise LedgerError('Unexpected or missing request fields')
    return body


def make_server(db, host='127.0.0.1', port=8765):
    ledger = db if isinstance(db, Ledger) else Ledger(db)

    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def send_json(self, value, status=200):
            payload = dumps(value).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(payload)

        def error(self, exc):
            self.close_connection = True
            self.send_json({'error': {'code': exc.code, 'message': str(exc)}}, exc.status)

        def do_GET(self):
            try:
                request = urlsplit(self.path)
                path, query = unquote(request.path), parse_qs(request.query, keep_blank_values=True)
                if path == '/v1/experiments':
                    self.send_json(ledger.status())
                elif path == '/v1/trials':
                    if set(query) - {'experiment_id', 'after', 'limit'} or any(len(v) != 1 for v in query.values()):
                        raise LedgerError('Unexpected or repeated query parameters')
                    if 'experiment_id' not in query:
                        raise LedgerError('experiment_id is required')
                    raw_limit = query.get('limit', ['50'])[0]
                    if len(raw_limit) > 3 or not raw_limit.isascii() or not raw_limit.isdecimal():
                        raise LedgerError('limit must be an integer')
                    self.send_json(ledger.trials(query['experiment_id'][0], query.get('after', [None])[0], int(raw_limit)))
                elif path.startswith('/v1/trials/') and path.endswith('/replay'):
                    trial_id = path[len('/v1/trials/'):-len('/replay')]
                    if '/' in trial_id:
                        raise LedgerError('Invalid trial ID')
                    self.send_json(ledger.replay(trial_id))
                elif path == '/' or path.startswith('/viewer/'):
                    viewer = (ROOT / 'viewer').resolve()
                    relative = 'index.html' if path == '/' else path[len('/viewer/'):]
                    target = (viewer / relative).resolve()
                    if not target.is_relative_to(viewer) or not target.is_file():
                        raise LedgerError('Not found', 'not_found', 404)
                    payload = target.read_bytes()
                    self.send_response(200)
                    mime = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
                    self.send_header('Content-Type', mime)
                    self.send_header('Content-Length', str(len(payload)))
                    self.send_header('X-Content-Type-Options', 'nosniff')
                    self.end_headers()
                    self.wfile.write(payload)
                else:
                    raise LedgerError('Not found', 'not_found', 404)
            except LedgerError as exc:
                self.error(exc)
            except (OSError, ValueError) as exc:
                self.error(LedgerError('Request could not be served', 'internal_error', 500))

        def do_POST(self):
            try:
                if self.headers.get('Transfer-Encoding'):
                    raise LedgerError('Transfer encoding is unsupported')
                lengths = self.headers.get_all('Content-Length', [])
                if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdecimal():
                    raise LedgerError('One valid Content-Length is required')
                if len(lengths[0]) > 10:
                    raise LedgerError('Request exceeds 16 MiB', 'payload_too_large', 413)
                length = int(lengths[0])
                if length > MAX_BODY:
                    raise LedgerError('Request exceeds 16 MiB', 'payload_too_large', 413)
                if self.headers.get_content_type() != 'application/json':
                    raise LedgerError('Content-Type must be application/json', 'unsupported_media_type', 415)
                self.connection.settimeout(30)
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise LedgerError('Incomplete request body')
                body = strict_json(raw)
                path = urlsplit(self.path).path
                if path == '/v1/lease':
                    fields(body, {'worker_id'})
                    self.send_json({'lease': ledger.acquire(body['worker_id'])})
                elif path == '/v1/heartbeat':
                    fields(body, {'task_id', 'worker_id', 'epoch'})
                    self.send_json(ledger.heartbeat(**body))
                elif path == '/v1/results':
                    fields(body, {'task_id', 'worker_id', 'epoch', 'results'})
                    self.send_json(ledger.submit(**body))
                else:
                    raise LedgerError('Not found', 'not_found', 404)
            except LedgerError as exc:
                self.error(exc)
            except (OSError, ValueError) as exc:
                self.error(LedgerError('Request could not be served', 'internal_error', 500))

    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    server.ledger = ledger
    return server


def run_pending(ledger, workers=2, node='node'):
    """All writes happen here; child processes execute only stateless leases."""
    from workers.cpu_worker import execute_lease
    integer(workers, 'workers', 1, 64)
    active = {}
    failed = False
    heartbeat_at = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        while True:
            while not failed and len(active) < workers:
                lease = ledger.acquire(f'local-{time.time_ns()}')
                if lease is None:
                    break
                active[pool.submit(execute_lease, lease, node)] = lease
            if not active:
                break
            done, _ = concurrent.futures.wait(active, timeout=1, return_when=concurrent.futures.FIRST_COMPLETED)
            if time.monotonic() - heartbeat_at >= 10:
                for lease in active.values():
                    ledger.heartbeat(lease['task_id'], lease['worker_id'], lease['epoch'])
                heartbeat_at = time.monotonic()
            for future in done:
                lease = active.pop(future)
                try:
                    results = future.result()
                    ledger.submit(lease['task_id'], lease['worker_id'], lease['epoch'], results)
                except Exception as exc:
                    failed = True
                    try:
                        ledger.release(lease['task_id'], lease['worker_id'], lease['epoch'], f'{type(exc).__name__}: {exc}')
                    except LedgerError:
                        pass
                    print(f"Task {lease['task_id']} failed: {exc}", file=sys.stderr)
    status = ledger.status()
    complete = all(e['accepted'] == e['total'] for e in status['experiments'])
    return status, not failed and complete


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('init', 'run', 'status', 'serve'):
        sub = commands.add_parser(name)
        sub.add_argument('--db', required=True)
        if name == 'init':
            sub.add_argument('--radius', type=float, default=.25)
            sub.add_argument('--duration', type=float, default=30)
            sub.add_argument('--dt', type=float, default=.002)
            sub.add_argument('--start', type=int, default=0)
            sub.add_argument('--count', type=int, default=60)
            sub.add_argument('--chunk-size', type=int, default=5)
            sub.add_argument('--node', default='node')
        elif name == 'run':
            sub.add_argument('--workers', type=int, default=2)
            sub.add_argument('--node', default='node')
        elif name == 'serve':
            sub.add_argument('--host', default='127.0.0.1')
            sub.add_argument('--port', type=int, default=8765)
    args = parser.parse_args(argv)
    try:
        ledger = Ledger(args.db)
        if args.command == 'init':
            from workers.cpu_worker import describe_manifest
            desc = describe_manifest({'radius': args.radius, 'duration': args.duration, 'dt': args.dt}, node=args.node)
            print(dumps(ledger.add_experiment(desc, args.start, args.count, args.chunk_size)))
        elif args.command == 'status':
            print(dumps(ledger.status()))
        elif args.command == 'run':
            status, ok = run_pending(ledger, args.workers, args.node)
            print(dumps(status))
            return 0 if ok else 1
        else:
            server = make_server(ledger, args.host, args.port)
            print(f'Pipeline viewer/API: http://{args.host}:{server.server_port}', flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
        return 0
    except (LedgerError, OSError, RuntimeError, ValueError) as exc:
        print(dumps({'error': {'code': getattr(exc, 'code', 'execution_error'), 'message': str(exc)}}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
