"""Independent review probes using actual reference output and HTTP publication."""
from concurrent.futures import ThreadPoolExecutor
import copy
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.ledger import Ledger
from services.pipeline import make_server
from workers.cpu_worker import describe_manifest, execute_lease


class IndependentPublicationTests(unittest.TestCase):
    def test_malformed_actual_result_is_atomic_and_structured(self):
        with tempfile.TemporaryDirectory() as folder:
            descriptor = describe_manifest({'radius': 2, 'duration': .02})
            ledger = Ledger(Path(folder) / 'review.sqlite')
            ledger.add_experiment(descriptor, 0, 1, 1)
            server = make_server(ledger, port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            origin = f'http://127.0.0.1:{server.server_port}'

            def post(route, value):
                request = Request(origin + route, json.dumps(value).encode(),
                                  headers={'Content-Type': 'application/json'})
                with urlopen(request, timeout=5) as response:
                    return json.load(response)

            try:
                lease = post('/v1/lease', {'worker_id': 'independent-review'})['lease']
                honest = execute_lease(lease)[0]
                identity = {key: lease[key] for key in ('task_id', 'worker_id', 'epoch')}
                mutations = {
                    'list_outcome': lambda r: r.update(outcome=[]),
                    'dict_outcome': lambda r: r.update(outcome={}),
                    'oversized_integer_time': lambda r: r.update(time=10**1000),
                    'oversized_integer_vector': lambda r: r['final']['p'].__setitem__(0, 10**1000),
                    'oversized_decimal_ordinal': lambda r: r.update(ordinal='9'*5000),
                    'impossible_recurrence': lambda r: r['orbit'].update(
                        detected=True, cycles=3, period=100, tolerance=999,
                        maxNormalizedError=1),
                    'different_solver_build': lambda r: r.update(solver_digest='0'*64),
                    'wrong_reconstructable_state': lambda r: r['initial']['p'].__setitem__(0, 0),
                }
                for label, mutate in mutations.items():
                    with self.subTest(label=label):
                        changed = copy.deepcopy(honest)
                        mutate(changed)
                        with self.assertRaises(HTTPError) as caught:
                            post('/v1/results', {**identity, 'results': [changed]})
                        self.assertEqual(caught.exception.code, 400)
                        error = json.loads(caught.exception.read())
                        self.assertEqual(error['error']['code'], 'invalid_request')
                        self.assertEqual(ledger.status()['experiments'][0]['accepted'], 0)
                self.assertEqual(post('/v1/results', {**identity, 'results': [honest]})['accepted'], 1)
                retry = post('/v1/results', {**identity, 'results': [honest]})
                self.assertTrue(retry['idempotent'])
                self.assertEqual(ledger.status()['experiments'][0]['accepted'], 1)
            finally:
                server.shutdown()
                thread.join(5)
                server.server_close()

    def test_concurrent_claims_have_unique_ranges(self):
        with tempfile.TemporaryDirectory() as folder:
            descriptor = describe_manifest({'radius': 2, 'duration': .02})
            ledger = Ledger(Path(folder) / 'race.sqlite')
            ledger.add_experiment(descriptor, 0, 3, 1)
            with ThreadPoolExecutor(max_workers=8) as pool:
                claims = list(pool.map(lambda i: ledger.acquire(f'review-{i}'), range(8)))
            leases = [claim for claim in claims if claim is not None]
            self.assertEqual(len(leases), 3)
            self.assertEqual(len({lease['task_id'] for lease in leases}), 3)
            self.assertEqual({lease['start'] for lease in leases}, {'0', '1', '2'})
            reopened = Ledger(Path(folder) / 'race.sqlite')
            self.assertIsNone(reopened.acquire('late-review'))
            self.assertEqual(reopened.status()['experiments'][0]['running'], 3)


if __name__ == '__main__':
    unittest.main()
