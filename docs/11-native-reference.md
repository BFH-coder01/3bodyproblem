# Native FP64 reference validation

This is a C++17 port of the accepted browser numerical functions. It is an isolated validation backend: the durable CPU pipeline continues to invoke its pinned JavaScript reference. No worker routing, protocol-v1 schema or physical model changes are made here.

## Build and run in a development environment

A local GNU-compatible C++17 compiler, Python 3.11+ and Node 18+ are required for the complete comparison. The build command installs nothing and records compiler version, flags, source hashes and the executable hash.

```bash
python3 scripts/build_native.py --out build/native-reference
./build/native-reference --describe --radius 2
./build/native-reference --radius 2 --ordinal 57 --duration 6 --dt 0.002
python3 scripts/compare_native.py --binary build/native-reference --out artifacts/native-parity.json
python3 -m unittest discover -s tests -p test_native_parity.py -v
```

The comparison command runs a fixed bounded sample from widely separated ordinal ranges, plus explicitly labelled numerical comparison fixtures. It reports source/build identity, event/classification differences and state errors. Nonzero-velocity figure-eight and rotating-triangle fixtures are reference tests; every enumerated search still starts at rest.

Raw replay frames follow the baseline sampling and event order. The existing JavaScript recurrence analyzer can read them for comparison; the native backend does not independently claim an orbit or stability proof. Close encounters remain stops, not mergers. All escapes retain the same meaning as the observation-square crossing.

The declared short-run tolerance is fixed in `contracts/native-reference-v1.md`: normalized absolute/relative error 1e-9 for position, velocity and energy at up to 0.1 simulated seconds. Grid enumeration and zero initial search velocities agree exactly. Trigonometric comparison fixtures can differ in their last floating-point bits across standard libraries; their initial velocities use the same predeclared tolerance. Longer chaotic state differences are reported alongside outcome and event timing rather than declared bitwise identical.

The header in native/include/ defines stateless functions. The CLI validates strict structured arguments and serializes finite JSON. Build outputs, sidecars and comparison report files remain outside Git; committed evidence records the commands, inputs, source/build hashes and test results.

## Scope and remaining gates

Cloud Linux compilation and comparison do not establish a valid Windows/HIP/ROCm tuple, actual RX 7900 XTX execution or physical multi-machine performance. No lab action is required while the user is on Android. Native worker enrollment needs a later reviewed adapter, an explicit build/precision capability policy and extended parity evidence. GPU smoke and batching follow only after an actual execution environment is available.

AddressSanitizer/UndefinedBehaviorSanitizer checks are separate from numerical parity. LeakSanitizer could not inspect the hosted container's process/thread state. The address/UB commands therefore disable leak scanning explicitly, locally and in CI, and do not claim a leak check. CI records its own address/UB outcome.
