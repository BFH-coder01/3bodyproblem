"""Real native compilation and cross-language physical/reference parity."""
import hashlib
import copy
import json
import math
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest
import sys

from scripts.compare_native import (ROOT, case_arguments, comparison, native_request,
                                    node_requests, run_report, strict_json)


class NativeParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts.build_native import build
        cls.folder = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.folder.cleanup)
        cls.binary = Path(cls.folder.name) / 'native-reference'
        cls.metadata = build(cls.binary)

    def native(self, *args):
        return native_request(self.binary, args)

    def test_describe_and_initial_state_extremes(self):
        for radius in (.1, .25, .3, 1, 2):
            with self.subTest(radius=radius):
                spec = node_requests([{'op': 'describe', 'radius': radius}])[0]
                actual = self.native('--describe', '--radius', radius)['grid']
                self.assertEqual(actual, {**{key: spec[key] for key in ('radius', 'n', 'N')}, 'total': str(spec['total'])})
                ordinals = sorted({0, 1, spec['N'] - 2, spec['total'] // 2, spec['total'] - 1})
                expected = node_requests([{'op': 'initial', 'radius': radius, 'ordinal': i} for i in ordinals])
                for ordinal, reference in zip(ordinals, expected):
                    envelope = self.native('--initial', '--radius', radius, '--ordinal', ordinal)
                    self.assertEqual(envelope['triple'], reference['scan']['triple'])
                    self.assertEqual(envelope['initial'], {'p': reference['p'], 'v': reference['v']})

    def test_every_small_radius2_grid_triple(self):
        # The smallest supported radius grid has25cells /2300distinct triples.
        # Batch Node once; native CLI is actually exercised for every ordinal.
        total = node_requests([{'op': 'describe', 'radius': 2}])[0]['total']
        expected = node_requests([{'op': 'initial', 'radius': 2, 'ordinal': i} for i in range(total)])
        for ordinal, reference in enumerate(expected):
            envelope = self.native('--initial', '--radius', 2, '--ordinal', ordinal)
            self.assertEqual(envelope['triple'], reference['scan']['triple'], ordinal)
            self.assertEqual(envelope['initial']['p'], reference['p'], ordinal)

    def test_accelerations_analytic_scaling_and_cancellation(self):
        examples = [[-3,-2,1,-1,2,3], [-2,0,0,0,2,0], [0,0,1,0,0,1], [0,0,2,0,0,2]]
        expected = node_requests([{'op': 'acceleration', 'p': p} for p in examples])
        actual = [self.native('--acceleration', *p)['acceleration'] for p in examples]
        for a, b in zip(actual, expected):
            for x, y in zip(a, b):
                self.assertAlmostEqual(x, y, delta=1e-12 * (1 + abs(y)))
            self.assertAlmostEqual(sum(a[::2]), 0, delta=1e-12)
            self.assertAlmostEqual(sum(a[1::2]), 0, delta=1e-12)
        self.assertEqual(actual[1][2:4], [0, 0])
        self.assertAlmostEqual(actual[2][0], 9.80665, delta=1e-12)
        for near, far in zip(actual[2], actual[3]):
            self.assertAlmostEqual(near, 4 * far, delta=1e-12)
        self.assertIsNone(self.native('--acceleration', 0,0,0,0,1,1)['acceleration'])

    def test_short_physical_state_parity_and_all_rest_motion(self):
        cases = [{'fixture': name, 'duration': .1, 'dt': .002} for name in
                 ('asymmetric-rest', 'collinear-rest', 'figure-eight', 'lagrange-triangle', 'fast-escape')]
        references = node_requests(cases)
        for case, reference in zip(cases, references):
            with self.subTest(case=case):
                actual = self.native(*case_arguments(case))['result']
                result = comparison(actual, reference, case)
                self.assertTrue(result['passed'], result)
                self.assertEqual(actual['frames'][0], [0, *actual['initial']['p']])
                self.assertEqual(actual['velocityFrames'][0], actual['initial']['v'])
                self.assertEqual(actual['frames'][-1][0], actual['time'])
                self.assertEqual(actual['velocityFrames'][-1], actual['finalVelocity'])
                self.assertEqual(len(actual['frames']), len(actual['velocityFrames']))
                self.assertLessEqual(len(actual['frames']), 1201)
                if case['fixture'] == 'asymmetric-rest':
                    self.assertEqual(actual['initial']['v'], [0] * 6)
                    for body in range(3):
                        self.assertGreater(math.dist(actual['initial']['p'][body*2:body*2+2],
                                                     actual['frames'][-1][body*2+1:body*2+3]), 0)

    def test_known_events_and_stateless_repeatability(self):
        cases = [{'radius': 2, 'ordinal': 57, 'duration': 6, 'dt': .002},
                 {'radius': .25, 'ordinal': 0, 'duration': 6, 'dt': .002}]
        references = node_requests(cases)
        first = None
        for case, reference in zip(cases, references):
            envelope = self.native(*case_arguments(case))
            self.assertTrue(comparison(envelope['result'], reference, case)['passed'])
            self.assertEqual(envelope['result']['initial']['v'], [0] * 6)
            if first is None:
                first = envelope
                self.assertEqual(first['result']['outcome'], 'Escaped')
                self.assertLess(first['result']['time'], 5)
            else:
                self.assertEqual(envelope['result']['outcome'], 'Close encounter')
        self.assertEqual(self.native(*case_arguments(cases[0])), first)

    def test_strict_cli_errors_do_not_emit_success(self):
        invalid = [['--unknown'], ['--radius'], ['--radius','nan'], ['--duration','inf'],
                   ['--dt','0'], ['--radius','0.01'], ['--duration','301'], ['--radius','0x1'],
                   ['--radius','1junk'], ['--ordinal','-1'], ['--ordinal','01'],
                   ['--ordinal','18446744073709551616'], ['--ordinal','999999999999999'],
                   ['--duration','1','--duration','2'], ['--fixture','figure-eight','--radius','2'],
                   ['--fixture','unknown'], ['--acceleration','1','2'],
                   ['--acceleration','0','0','1','0','0','1','--dt','.001'],
                   ['--initial','--describe'], ['--describe','--ordinal','0']]
        for arguments in invalid:
            with self.subTest(arguments=arguments):
                run = subprocess.run([str(self.binary), *arguments], text=True, capture_output=True, timeout=10)
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertEqual(run.stdout, '')
                self.assertEqual(strict_json(run.stderr)['error']['code'], 'invalid_input')

    def test_bounded_comparison_report_with_source_identity(self):
        report = run_report(self.binary)
        self.assertTrue(report['passed'], [case for case in report['cases'] if not case['passed']])
        self.assertEqual(report['binary_sha256'], hashlib.sha256(self.binary.read_bytes()).hexdigest())
        self.assertGreaterEqual(report['case_count'], 20)
        self.assertEqual(report['disagreement_count'], 0)
        self.assertEqual(report['verified_build_metadata']['build_id'], self.metadata['build_id'])
        self.assertEqual(report['verified_build_metadata']['flags'], self.metadata['flags'])
        for name, digest in report['source_sha256'].items():
            self.assertEqual(digest, hashlib.sha256((ROOT / name).read_bytes()).hexdigest())

    def test_report_rejects_missing_stale_or_tampered_build_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = Path(folder) / self.binary.name
            shutil.copyfile(self.binary, binary)
            binary.chmod(0o755)
            sidecar = binary.with_name(binary.name + '.build.json')
            with self.assertRaisesRegex(ValueError, 'sidecar is required'):
                run_report(binary)
            mutations = [
                ('binary hash', lambda m: m.update(binary_sha256='0' * 64)),
                ('source hashes', lambda m: m['sources_sha256'].update({'native/core/threebody.cpp': '0' * 64})),
                ('build flags', lambda m: m['flags'].append('-ffast-math')),
                ('build identity', lambda m: m.update(build_id='0' * 64)),
                ('compiler', lambda m: m.update(compiler='a different compiler')),
            ]
            for label, mutate in mutations:
                with self.subTest(label=label):
                    metadata = copy.deepcopy(self.metadata)
                    mutate(metadata)
                    sidecar.write_text(json.dumps(metadata))
                    with self.assertRaises(ValueError):
                        run_report(binary)
            sidecar.write_text(json.dumps(self.metadata))
            # Binary corruption must fail provenance before attempting execution.
            binary.write_bytes(binary.read_bytes() + b'changed')
            with self.assertRaisesRegex(ValueError, 'binary hash'):
                run_report(binary)

    def test_documented_report_cli_from_arbitrary_working_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            output = folder / 'nested' / 'parity.json'
            command = [sys.executable, str(ROOT / 'scripts/compare_native.py'),
                       '--binary', str(self.binary), '--out', str(output)]
            run = subprocess.run(command, cwd=folder, capture_output=True, text=True, timeout=180)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stderr, '')
            self.assertTrue(strict_json(run.stdout)['passed'])
            self.assertTrue(strict_json(output.read_text())['passed'])
            bad_binary = folder / 'bad-reference'
            shutil.copyfile(self.binary, bad_binary)
            bad_binary.chmod(0o755)
            metadata = copy.deepcopy(self.metadata)
            metadata['binary_sha256'] = '0' * 64
            bad_binary.with_name(bad_binary.name + '.build.json').write_text(json.dumps(metadata))
            failed_output = folder / 'must-not-exist.json'
            command = [sys.executable, str(ROOT / 'scripts/compare_native.py'),
                       '--binary', str(bad_binary), '--out', str(failed_output)]
            run = subprocess.run(command, cwd=folder, capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(run.stdout, '')
            self.assertIn('binary hash', strict_json(run.stderr)['error'])
            self.assertNotIn('Traceback', run.stderr)
            self.assertFalse(failed_output.exists())

    def test_comparison_handles_unavailable_energy_and_preserves_exact_rest(self):
        case = {'radius': 2, 'ordinal': 0, 'duration': .1, 'dt': .002}
        reference = node_requests([case])[0]
        actual = self.native(*case_arguments(case))['result']
        reference = copy.deepcopy(reference)
        actual = copy.deepcopy(actual)
        # Singular diagnostics are null at the JSON boundary. Their absence must
        # be explicit, not a max(empty) exception or a fabricated zero error.
        for key in ('initialEnergy', 'finalEnergy'):
            reference[key] = actual[key] = None
        report = comparison(actual, reference, case)
        self.assertTrue(report['passed'], report)
        self.assertIsNone(report['normalized_energy_error'])
        self.assertEqual(report['unavailable_energy_diagnostics'], ['initialEnergy', 'finalEnergy'])
        actual['initial']['v'][0] = 1e-16
        self.assertIn('scan state does not start exactly at rest', comparison(actual, reference, case)['failures'])
        reference['initial']['v'][0] = 0
        fixture_case = {'fixture': 'comparison-only', 'duration': .1, 'dt': .002}
        self.assertTrue(comparison(actual, reference, fixture_case)['passed'])


if __name__ == '__main__':
    unittest.main()
