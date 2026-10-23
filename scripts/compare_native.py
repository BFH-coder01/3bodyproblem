"""Bounded, reproducible native FP64 / unchanged JavaScript comparison.

This is a validation tool, never a production worker/backend selector.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SHORT_TOLERANCE = 1e-9
NODE_PROGRAM = r'''
const fs=require('node:fs');
const P=require('./baseline/dist/physics.js'), S=require('./baseline/dist/scan.js');
function state(q) {
 if (!q.fixture) return S.initial(q.radius,q.ordinal);
 if (q.fixture==='figure-eight') return P.preset('eight');
 if (q.fixture==='lagrange-triangle') return P.preset('triangle');
 if (q.fixture==='asymmetric-rest') return {p:[-3,-2,1,-1,2,3],v:Array(6).fill(0)};
 if (q.fixture==='collinear-rest') return {p:[-2,0,0,0,2,0],v:Array(6).fill(0)};
 if (q.fixture==='fast-escape') return {p:[-2,0,0,0,2,0],v:[-20,0,0,0,20,0]};
 throw Error('Unsupported fixed fixture');
}
const out=JSON.parse(fs.readFileSync(0,'utf8')).map(q=>{
 if(q.op==='describe') return S.spec(q.radius);
 if(q.op==='initial') return S.initial(q.radius,q.ordinal);
 if(q.op==='triple') return S.tripleAt(q.N,q.ordinal);
 if(q.op==='acceleration') return P.acc(q.p);
 let initial=state(q), sim=P.create(initial,{duration:q.duration,dt:q.dt});
 while(!sim.advance(20000)){}
 let r=sim.result;
 return {...r,initialEnergy:P.energy(initial.p,initial.v),finalEnergy:P.energy(r.frames.at(-1).slice(1),r.finalVelocity)};
});
process.stdout.write(JSON.stringify(out));
'''


def strict_json(text):
    def invalid(value):
        raise ValueError(f'Nonfinite JSON token {value}')
    result = json.loads(text, parse_constant=invalid)
    def finite(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError('Nonfinite JSON value')
        if isinstance(value, dict):
            for part in value.values():
                finite(part)
        elif isinstance(value, list):
            for part in value:
                finite(part)
    finite(result)
    return result


def node_requests(requests):
    run = subprocess.run(['node', '-e', NODE_PROGRAM], cwd=ROOT,
                         input=json.dumps(requests, allow_nan=False), text=True,
                         capture_output=True, timeout=180, check=True)
    return strict_json(run.stdout)


def native_request(binary, arguments):
    run = subprocess.run([str(binary), *map(str, arguments)], text=True,
                         capture_output=True, timeout=180, check=True)
    response = strict_json(run.stdout)
    if response.get('protocol') != 'threebody.native-reference.v1':
        raise ValueError('Native response has unexpected protocol')
    if response.get('engine') != 'native-fp64-v1':
        raise ValueError('Native response has unexpected engine')
    build = response.get('build', {})
    if build.get('precision') != 'fp64' or build.get('fast_math') is not False:
        raise ValueError('Native response does not identify strict FP64 build')
    return response


def case_arguments(case):
    arguments = ['--fixture', case['fixture']] if 'fixture' in case else [
        '--radius', str(case['radius']), '--ordinal', str(case['ordinal'])]
    return arguments + ['--duration', str(case['duration']), '--dt', str(case.get('dt', .002))]


def numeric_error(actual, expected):
    if len(actual) != len(expected):
        raise ValueError('Comparison vectors have different sizes')
    return max((abs(a - b) / (1 + abs(b)) for a, b in zip(actual, expected)), default=0)


def comparison(native, reference, case):
    """Return explicit acceptance failures; never adjust tolerances to fit output."""
    errors = []
    short = case['duration'] <= .1
    dt = case.get('dt', .002)
    event_tolerance = max(1e-8, 4 * dt)
    if native['outcome'] != reference['outcome']:
        errors.append('outcome disagreement')
    time_error = abs(native['time'] - reference['time'])
    if time_error > event_tolerance:
        errors.append('event time outside fixed bound')
    position_error = numeric_error(native['frames'][-1][1:], reference['frames'][-1][1:])
    velocity_error = numeric_error(native['finalVelocity'], reference['finalVelocity'])
    initial_error = numeric_error(native['initial']['p'], reference['initial']['p'])
    initial_velocity_error = numeric_error(native['initial']['v'], reference['initial']['v'])
    if initial_error > SHORT_TOLERANCE or initial_velocity_error > SHORT_TOLERANCE:
        errors.append('initial state outside fixed 1e-9 bound')
    # Trigonometric comparison fixtures use the predeclared state tolerance.
    # Actual enumerated search trials must still have exactly zero velocity.
    if 'fixture' not in case and (native['initial']['v'] != [0] * 6 or reference['initial']['v'] != [0] * 6):
        errors.append('scan state does not start exactly at rest')
    energy_errors, unavailable_energy = [], []
    for key in ('initialEnergy', 'finalEnergy'):
        actual_energy, expected_energy = native[key], reference[key]
        if actual_energy is None or expected_energy is None:
            unavailable_energy.append(key)
            if (actual_energy is None) != (expected_energy is None):
                errors.append(f'{key} availability disagreement')
        else:
            energy_errors.append(numeric_error([actual_energy], [expected_energy]))
    energy_error = max(energy_errors, default=None)
    if short:
        if position_error > SHORT_TOLERANCE:
            errors.append('short position parity outside 1e-9')
        if velocity_error > SHORT_TOLERANCE:
            errors.append('short velocity parity outside 1e-9')
        if energy_error is not None and energy_error > SHORT_TOLERANCE:
            errors.append('short energy parity outside 1e-9')
    return {'passed': not errors, 'failures': errors, 'short_state_tolerance': SHORT_TOLERANCE if short else None,
            'event_time_tolerance': event_tolerance, 'event_time_error': time_error,
            'normalized_initial_position_error': initial_error,
            'normalized_initial_velocity_error': initial_velocity_error,
            'normalized_position_error': position_error, 'normalized_velocity_error': velocity_error,
            'normalized_energy_error': energy_error, 'unavailable_energy_diagnostics': unavailable_energy,
            'native_outcome': native['outcome'],
            'reference_outcome': reference['outcome'], 'native_time': native['time'],
            'reference_time': reference['time'], 'native_steps': native['steps'],
            'reference_steps': reference['steps']}


def sampled_cases():
    grids = node_requests([{'op': 'describe', 'radius': radius} for radius in (.1, .25, 2)])
    cases = []
    for radius, grid in zip((.1, .25, 2), grids):
        for ordinal in (0, grid['total'] // 2, grid['total'] - 1):
            cases.append({'radius': radius, 'ordinal': ordinal, 'duration': .1, 'dt': .002})
    cases += [{'fixture': name, 'duration': .1, 'dt': .002}
              for name in ('asymmetric-rest', 'collinear-rest', 'figure-eight', 'lagrange-triangle', 'fast-escape')]
    cases += [{'radius': 2, 'ordinal': ordinal, 'duration': 6, 'dt': .002} for ordinal in (0, 28, 57, 500, 1000, 2299)]
    cases += [{'fixture': 'figure-eight', 'duration': 20, 'dt': .001},
              {'fixture': 'lagrange-triangle', 'duration': 3, 'dt': .002}]
    return cases


def verified_build(binary):
    """Check the builder's recorded source/flags/binary linkage before execution.

    This verifies metadata integrity against current files, not remote execution
    or authenticity against a malicious publisher able to forge all metadata.
    """
    if __package__:
        from .build_native import FLAGS, SOURCES
    else:
        # Direct ``python /path/to/scripts/compare_native.py`` sets sys.path[0]
        # to scripts/, including when launched outside the repository root.
        from build_native import FLAGS, SOURCES
    sidecar = binary.with_name(binary.name + '.build.json')
    try:
        raw = sidecar.read_bytes()
    except OSError as exc:
        raise ValueError('Native build metadata sidecar is required') from exc
    if len(raw) > 65536:
        raise ValueError('Native build metadata exceeds 64 KiB')
    metadata = strict_json(raw)
    if not isinstance(metadata, dict) or metadata.get('format') != 'threebody.native-build.v1':
        raise ValueError('Unsupported native build metadata')
    if metadata.get('precision') != 'fp64' or metadata.get('fast_math') is not False:
        raise ValueError('Native metadata does not declare strict FP64')
    if metadata.get('flags') != list(FLAGS):
        raise ValueError('Native build flags differ from the accepted builder policy')
    compiler = metadata.get('compiler')
    if not isinstance(compiler, str) or not compiler.strip() or len(compiler) > 4096:
        raise ValueError('Native compiler identity is missing or malformed')
    sources = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}
    if metadata.get('sources_sha256') != sources:
        raise ValueError('Native source hashes do not match current source')
    descriptor = json.dumps({'sources': sources, 'flags': list(FLAGS), 'compiler': compiler},
                            sort_keys=True, separators=(',', ':')).encode()
    if metadata.get('build_id') != hashlib.sha256(descriptor).hexdigest():
        raise ValueError('Native build identity is inconsistent with compiler, flags and source')
    if metadata.get('binary_sha256') != hashlib.sha256(binary.read_bytes()).hexdigest():
        raise ValueError('Native binary hash does not match its build metadata')
    return metadata


def run_report(binary):
    binary = Path(binary).resolve()
    metadata = verified_build(binary)
    cases = sampled_cases()
    references = node_requests(cases)
    entries = []
    build = None
    for case, reference in zip(cases, references):
        envelope = native_request(binary, case_arguments(case))
        build = envelope['build']
        entries.append({'input': case, **comparison(envelope['result'], reference, case)})
    source_paths = ['baseline/dist/physics.js', 'baseline/dist/scan.js', 'native/include/threebody.hpp',
                    'native/core/threebody.cpp', 'native/cli/main.cpp', 'scripts/compare_native.py']
    return {'protocol': 'threebody.native-parity-report.v1', 'passed': all(e['passed'] for e in entries),
            'binary_sha256': metadata['binary_sha256'], 'build': build,
            'verified_build_metadata': metadata,
            'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_paths},
            'case_count': len(entries), 'disagreement_count': sum(not e['passed'] for e in entries),
            'cases': entries, 'limits': ['Validation-only native CLI; production pipeline unchanged.',
                                       'Long chaotic final-state differences are reported, not asserted bitwise equal.',
                                       'Build metadata linkage verified; not attestation against a malicious publisher.',
                                       'No GPU, Windows, physical multi-machine or permanent stability claim.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True)
    parser.add_argument('--out')
    args = parser.parse_args(argv)
    try:
        report = run_report(args.binary)
        rendered = json.dumps(report, indent=2, allow_nan=False) + '\n'
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(rendered)
            print(json.dumps({'passed': report['passed'], 'case_count': report['case_count'],
                              'disagreement_count': report['disagreement_count'], 'out': args.out}))
        else:
            print(rendered, end='')
        return 0 if report['passed'] else 1
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
