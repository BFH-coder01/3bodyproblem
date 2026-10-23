# Native reference evidence — 23 October 2026

Reviewed implementation head: `239adb2697408173754bf2d9397b2f6929f554f9`. Agent worktrees/author heads are recorded in ops/native-handoffs.json; the published PR records the equivalent final source tree and remote head.

Environment: hosted Linux CPU, GCC 13.3.0, IEEE binary64, C++17, -O2 -fno-fast-math -ffp-contract=off. No new packages, driver changes, GPU execution, public deployment or physics-model changes.

## Executed acceptance

- `python3 -m unittest discover -s tests -v`: 36 tests passed, including 10 native tests and the existing 26 pipeline/workspace/inventory tests.
- `python3 -m unittest verification.native_reference_adversarial -v`: 6 independent native probes passed.
- `python3 -m unittest discover -s verification -v`: 2 previous independent publication probes passed.
- All 3 existing Node suites passed (baseline physics, stateless reference, viewer-model).
- Native C++ analytic/edge tests passed with strict FP flags; separate AddressSanitizer/UndefinedBehaviorSanitizer run passed with leak detection explicitly disabled.
- The documented standalone comparison command passed from both the repository and an unrelated working directory without PYTHONPATH.
- 2,300 radius 2 grid initializations were compared exactly, plus sampled boundary/extreme ordinals for other radii.
- Source/build-linked 22-case report: zero failures under the declared policy. Maximum short-run normalized position error approximately 7.90e-17 and velocity error 9.45e-17, below the fixed 1e-9 bound.
- The native figure-eight raw record passes the unchanged JavaScript recurrence screen: 3 cycles, period 5.713338304503539, normalized error about0.00129834. This is a nonzero-velocity comparison fixture, not an all-rest search result or proof of permanent stability.
- The actual all-rest radius 2 ordinal 57 escapes at about 4.7683 simulated seconds, preserving eligibility below 5 seconds.
- `git diff --exit-code d5cf534 -- baseline workers services viewer`: clean; the production pipeline is untouched.

## Review findings and limits

The independent verifier reproduced and rechecked fixes for extreme-coordinate arithmetic, nonfinite returned physical states, raw non-UTF8 argv reflected into JSON diagnostics, stale-binary provenance, and a direct-script import failure missed by module-only tests. Tests enforce these defects rather than merely asserting implementation structure. Trigonometric fixture initial velocities use the already-declared 1e-9 state bound; enumerated velocities remain exactly zero.

The initial default LeakSanitizer attempt failed because the hosted runtime could not read process/thread state under its tracing restrictions. ASan/UBSan was then run explicitly with ASAN_OPTIONS=detect_leaks=0; no leak check is claimed, and CI uses the same declared scope.

The 22-case sample is a bounded validation set, not an exhaustive numerical classification agreement claim. Native worker enrollment, heterogeneous hardware behavior, Windows/HIP/ROCm, actual 7900 XTX performance and rendered-browser acceptance remain pending. No CPU result is labelled GPU success.

See verification/native_reference_review.md for the independent evidence and ops/evidence/NATIVE-PARITY.json for per-case metrics, source hashes, compiler/build identity and executable digest. Build binaries/sidecars and full motion data stay outside Git.
