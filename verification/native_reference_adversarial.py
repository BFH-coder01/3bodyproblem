"""Independent real-binary/core checks, authored outside implementation agents."""
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NativeIndependentVerification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts.build_native import build
        cls.folder = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.folder.cleanup)
        cls.binary = Path(cls.folder.name) / 'reference'
        cls.metadata = build(cls.binary)

    def invoke(self, *args):
        return subprocess.run([str(self.binary), *map(str, args)], capture_output=True, timeout=60)

    def test_finite_extreme_acceleration_is_rejected_not_null_vector(self):
        for p in ([1e308, 0, -1e308, 0, 0, 1e308],
                  [1.3e308, 1.3e308, 0, 0, 1, 1]):
            result = self.invoke('--acceleration', *p)
            self.assertEqual(result.returncode, 2, result.stdout)
            self.assertEqual(result.stdout, b'')
            self.assertEqual(json.loads(result.stderr)['error']['code'], 'invalid_input')
        contact = self.invoke('--acceleration', 0, 0, 0, 0, 1, 1)
        self.assertEqual(contact.returncode, 0)
        self.assertIsNone(json.loads(contact.stdout)['acceleration'])

    def test_invalid_utf8_argument_still_has_valid_error_json(self):
        if os.name == 'nt':
            self.skipTest('Raw byte argv is a POSIX-only boundary; Windows remains separately untested')
        result = subprocess.run([os.fsencode(self.binary), b'--\xff'], capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')
        self.assertEqual(json.loads(result.stderr.decode('utf-8'))['error']['code'], 'invalid_input')

    def test_native_record_passes_unchanged_orbit_screen(self):
        result = self.invoke('--fixture', 'figure-eight', '--duration', 20, '--dt', .001)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(result.stdout)['result']
        self.assertEqual(record['outcome'], 'Bounded')
        screened = subprocess.run([
            'node', '-e', "const fs=require('node:fs'),O=require('./baseline/dist/orbit.js');process.stdout.write(JSON.stringify(O.analyze(JSON.parse(fs.readFileSync(0,'utf8')))));"
        ], cwd=ROOT, input=json.dumps(record), capture_output=True, text=True, timeout=20, check=True)
        orbit = json.loads(screened.stdout)
        self.assertTrue(orbit['detected'], orbit)
        self.assertEqual(orbit['cycles'], 3)
        self.assertLess(abs(orbit['period'] - 5.713), .03)

    def test_parity_report_rejects_unlinked_binary_provenance(self):
        from scripts.compare_native import run_report
        copied = Path(self.folder.name) / 'unlinked-reference'
        shutil.copy2(self.binary, copied)
        sidecar = copied.with_name(copied.name + '.build.json')
        with self.assertRaises((ValueError, OSError)):
            run_report(copied)
        metadata = dict(self.metadata)
        metadata['binary_sha256'] = '0' * 64
        sidecar.write_text(json.dumps(metadata))
        with self.assertRaises((ValueError, OSError)):
            run_report(copied)
        metadata = json.loads(json.dumps(self.metadata))
        metadata['sources_sha256']['native/core/threebody.cpp'] = '0' * 64
        sidecar.write_text(json.dumps(metadata))
        with self.assertRaises((ValueError, OSError)):
            run_report(copied)

    def test_documented_report_script_executes_as_a_real_cli(self):
        report_path = Path(self.folder.name) / 'direct-cli-report.json'
        environment = dict(os.environ)
        environment.pop('PYTHONPATH', None)
        result = subprocess.run([
            sys.executable, str(ROOT / 'scripts/compare_native.py'), '--binary', str(self.binary),
            '--out', str(report_path)
        ], cwd=self.folder.name, env=environment, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['passed'])
        report = json.loads(report_path.read_text())
        self.assertTrue(report['passed'])
        self.assertEqual(report['case_count'], 22)

    def test_public_core_overflow_bounds_and_state_isolation(self):
        source = Path(self.folder.name) / 'independent.cpp'
        source.write_text(r'''
#include "threebody.hpp"
#include <cassert>
#include <cmath>
#include <limits>
#include <stdexcept>
using namespace threebody;
void finite(const Vec6& v) { for(double x:v) assert(std::isfinite(x)); }
int main() {
  for(auto n: {std::uint64_t(0),std::uint64_t(2),std::uint64_t(14162),std::numeric_limits<std::uint64_t>::max()}) {
    bool rejected=false; try { triple_at(n,0); } catch(const std::invalid_argument&) { rejected=true; }
    assert(rejected);
  }
  const State original=fixture("asymmetric-rest");
  const auto before=original;
  const auto first=simulate(original,{.1,.002});
  simulate(fixture("fast-escape"),{1,.002});
  const auto repeated=simulate(original,{.1,.002});
  assert(original.p==before.p && original.v==before.v);
  assert(first.final.p==repeated.final.p && first.final.v==repeated.final.v);
  assert(first.frames==repeated.frames && first.velocity_frames==repeated.velocity_frames);
  State extreme{{std::numeric_limits<double>::max(),0,0,1,0,-1},{1e308,0,0,0,0,0}};
  try {
    const auto r=simulate(extreme,{.01,.002});
    finite(r.initial.p); finite(r.initial.v); finite(r.final.p); finite(r.final.v);
    for(const auto& f:r.frames) for(double x:f) assert(std::isfinite(x));
    for(const auto& v:r.velocity_frames) finite(v);
  } catch(const std::invalid_argument&) {}
  const auto singular=simulate(State{{0,0,0,0,1,1},{}},{1,.002});
  assert(singular.outcome=="Close encounter" && singular.time==0);
  assert(std::isinf(singular.initial_energy));
  assert(singular.frames.size()==1);
}
''')
        binary = Path(self.folder.name) / 'independent'
        subprocess.run(['c++', '-std=c++17', '-O2', '-fno-fast-math', '-ffp-contract=off',
                        '-I', str(ROOT / 'native/include'), str(ROOT / 'native/core/threebody.cpp'),
                        str(source), '-o', str(binary)], check=True, capture_output=True, timeout=120)
        subprocess.run([str(binary)], check=True, capture_output=True, timeout=20)


if __name__ == '__main__':
    unittest.main()
