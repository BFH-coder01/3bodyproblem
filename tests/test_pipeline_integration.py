"""Real process/HTTP integration; no mocked simulation or ledger."""
import contextlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request

from workers.cpu_worker import describe_manifest, execute_lease, remote_worker

ROOT = Path(__file__).resolve().parents[1]


def cli(*args):
    result = subprocess.run([sys.executable, '-m', 'services.pipeline', *args],
                            cwd=ROOT, capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise AssertionError(f'CLI failed {args}: {result.stdout}\n{result.stderr}')
    return result.stdout


@contextlib.contextmanager
def serving(db):
    from services.pipeline import make_server
    server = make_server(str(db), '127.0.0.1', 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_address[1]}'
    finally:
        server.shutdown()
        thread.join(5)
        server.server_close()


def get(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.load(response)


class PipelineIntegration(unittest.TestCase):
    def test_reference_supervisor_runs_without_shared_state(self):
        descriptor = describe_manifest({'radius': 2, 'duration': 6})
        lease = {**descriptor, 'start': '57', 'end': '58'}
        result = execute_lease(lease)[0]
        self.assertEqual(result['outcome'], 'Escaped')
        self.assertLess(result['time'], 5)
        self.assertTrue(result['replayEligible'])
        self.assertIsNotNone(result['replay'])
        self.assertEqual(result, execute_lease(lease)[0])
        with self.assertRaises(ValueError):
            execute_lease({**lease, 'start': '057'})
        with self.assertRaises(ValueError):
            execute_lease({**lease, 'end': '100'})
        with self.assertRaises(RuntimeError):
            execute_lease({**lease, 'solver_digest': '0' * 64})

    def test_local_multiprocess_restart_and_real_replay_api(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / 'campaign.sqlite'
            cli('init', '--db', str(db), '--radius', '2', '--duration', '6',
                '--count', '60', '--chunk-size', '5')
            cli('run', '--db', str(db), '--workers', '2')
            status = json.loads(cli('status', '--db', str(db)))['experiments'][0]
            self.assertEqual(status['accepted'], 60)
            self.assertEqual(status['pending'], 0)
            self.assertEqual(status['running'], 0)
            # Reopening/rerunning a complete campaign adds no duplicate results.
            cli('run', '--db', str(db), '--workers', '2')
            self.assertEqual(json.loads(cli('status', '--db', str(db)))['experiments'][0]['accepted'], 60)
            with serving(db) as url:
                descriptor = get(url + '/v1/experiments')['experiments'][0]
                experiment_id = descriptor['experiment_id']
                all_trials, after = [], None
                while True:
                    query = {'experiment_id': experiment_id, 'limit': 7}
                    if after is not None:
                        query['after'] = after
                    page = get(url + '/v1/trials?' + urllib.parse.urlencode(query))
                    all_trials.extend(page['trials'])
                    after = page['next_after']
                    if after is None:
                        break
                self.assertEqual([r['ordinal'] for r in all_trials], [str(i) for i in range(60)])
                escaped = all_trials[57]
                self.assertEqual(escaped['outcome'], 'Escaped')
                replay = get(url + '/v1/trials/' + escaped['trial_id'] + '/replay')
                self.assertEqual(replay['replay']['frames'][0][0], 0)
                self.assertEqual(replay['replay']['frames'][-1][1:], escaped['final']['p'])
                self.assertLess(replay['time'], 5)
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    get(url + '/v1/trials/' + all_trials[0]['trial_id'] + '/replay')
                self.assertEqual(caught.exception.code, 404)
                with urllib.request.urlopen(url, timeout=10) as response:
                    self.assertIn(b'<canvas', response.read())

    def test_actual_http_worker_publishes_and_then_stops(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / 'remote.sqlite'
            cli('init', '--db', str(db), '--radius', '2', '--duration', '6',
                '--start', '57', '--count', '3', '--chunk-size', '2')
            with serving(db) as url:
                count = remote_worker(url, 'http-integration-worker')
                self.assertEqual(count, 3)
                self.assertEqual(remote_worker(url, 'http-integration-worker'), 0)
                status = get(url + '/v1/experiments')['experiments'][0]
                self.assertEqual(status['accepted'], 3)
                self.assertEqual(status['pending'], 0)


if __name__ == '__main__':
    unittest.main()
