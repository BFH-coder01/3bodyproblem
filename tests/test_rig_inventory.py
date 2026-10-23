import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock

SPEC = importlib.util.spec_from_file_location('rig_inventory', Path(__file__).resolve().parents[1] / 'scripts/rig_inventory.py')
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)


class InventoryTests(unittest.TestCase):
    def test_missing_tool_is_explicit_and_never_launched(self):
        run = Mock()
        report = inventory.probe(['missing', '--version'], which=lambda _: None, runner=run)
        self.assertEqual(report['status'], 'missing')
        self.assertIsNone(report['returncode'])
        run.assert_not_called()

    def test_timeout_retains_bounded_partial_evidence(self):
        run = Mock(side_effect=subprocess.TimeoutExpired('rocminfo', 10, output=b'partial', stderr=b'waiting'))
        report = inventory.probe(['rocminfo'], which=lambda _: '/fake/rocminfo', runner=run)
        self.assertEqual(report['status'], 'timeout')
        self.assertEqual(report['stdout'], 'partial')
        self.assertEqual(report['stderr'], 'waiting')
        self.assertEqual(run.call_args.args[0], ['/fake/rocminfo'])
        self.assertNotIn('shell', run.call_args.kwargs)
        self.assertEqual(run.call_args.kwargs['timeout'], 10)

    def test_nonzero_exit_and_long_output_are_visible(self):
        run = Mock(return_value=subprocess.CompletedProcess([], 2, 'x' * 30_000, 'bad option'))
        report = inventory.probe(['hipcc', '--version'], which=lambda _: '/fake/hipcc', runner=run)
        self.assertEqual(report['status'], 'error')
        self.assertEqual(report['returncode'], 2)
        self.assertTrue(report['truncated'])
        self.assertEqual(len(report['stdout']), inventory.OUTPUT_LIMIT)

    def test_launch_failure_is_explicit(self):
        run = Mock(side_effect=OSError(13, 'Permission denied'))
        report = inventory.probe(['hipcc', '--version'], which=lambda _: '/fake/hipcc', runner=run)
        self.assertEqual(report['status'], 'error')
        self.assertIn('Permission denied', report['stderr'])

    def test_linux_structure_and_no_false_gpu_success(self):
        def probe(command):
            stdout = {'node': 'v24.1.0', 'git': 'git version 2.1',
                      'lspci': '01:00 VGA compatible controller: AMD Example\n02:00 Network controller: omit me'}
            return {'status': 'ok' if command[0] in stdout else 'missing', 'stdout': stdout.get(command[0], ''), 'stderr': ''}
        report = inventory.collect(system='Linux', run_probe=probe)
        self.assertEqual(report['schema_version'], 'threebody.rig-inventory.v1')
        self.assertEqual(len(report['gpu']['devices']), 1)
        self.assertNotIn('Network controller', json.dumps(report))
        self.assertEqual(report['tools']['hipcc']['status'], 'missing')
        self.assertEqual(report['assessment']['gpu_execution']['status'], 'not_tested')
        self.assertTrue(report['assessment']['cpu_pipeline']['ready'])
        self.assertNotIn('environ', report)
        self.assertNotIn('node', report['platform'])
        json.dumps(report, allow_nan=False)

    def test_windows_controller_fields_are_limited_and_ram_not_inferred(self):
        commands = []
        def probe(command):
            commands.append(command)
            if command[0] == 'powershell':
                return {'status': 'ok', 'stdout': json.dumps({'Name': 'Example GPU', 'PNPDeviceID': 'PCI EXAMPLE', 'DriverVersion': '1', 'AdapterRAM': 1, 'Other': 'excluded'})}
            return {'status': 'missing', 'stdout': ''}
        report = inventory.collect(system='Windows', run_probe=probe)
        self.assertEqual(set(report['gpu']['devices'][0]), {'Name', 'PNPDeviceID', 'DriverVersion'})
        self.assertEqual(report['assessment']['gpu_execution']['status'], 'not_tested')
        self.assertFalse(report['assessment']['cpu_pipeline']['ready'])
        self.assertEqual([c[0] for c in commands], ['git', 'node', 'hipcc', 'powershell'])
        self.assertNotIn('AdapterRAM', commands[-1][-1])

    def test_unsupported_os_and_bad_controller_json_are_explicit(self):
        fake = lambda command: {'status': 'missing', 'stdout': ''}
        other = inventory.collect(system='OtherOS', run_probe=fake)
        self.assertEqual(other['tools']['gpu_detection']['status'], 'not_applicable')
        windows = inventory.collect(system='Windows', run_probe=lambda command: {'status': 'ok', 'stdout': 'not-json'})
        self.assertEqual(windows['gpu']['devices'], [])
        self.assertIn('invalid or truncated JSON', windows['gpu']['notes'][0])


if __name__ == '__main__':
    unittest.main()
