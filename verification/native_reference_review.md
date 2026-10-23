# NAT-060 independent native reference review

Reviewer: a separate Codex agent that authored no numerical, CLI, build or parity implementation. The review is independent model evidence under the same GitHub account, not a forged distinct-actor GitHub approval.

Initial reviewed head: `7cd64f636b3ddf71f3f983df45d74c8eba4b7b08`.
First corrected implementation head: `4986033b861d1526062ae41efdd9147aa55e31cb`.
Final reviewed implementation head: `239adb2697408173754bf2d9397b2f6929f554f9`.

Scope: additive C++17 FP64 reference functions, argv/JSON CLI, reproducible build metadata and comparison harness. Existing production pipeline protocol and backend selection remain unchanged.

## Findings and owner fixes

1. **Finite acceleration overflow, medium.** Actual CLI invocation with positions `[1e308,0,-1e308,0,0,1e308]` exited successfully with `acceleration:[null,0,null,0,0,0]`: finite coordinates overflowed intermediate displacement arithmetic. The contract requires six finite numbers or whole-null close-encounter classification. The core owner fixed the public acceleration boundary in `c7abc222eee5d8c25013e6ce57a16cbc78a83715`; overflow inputs now reject without invalid physical vectors.
2. **Finite simulation-state overflow, medium.** A direct public-core State with `p[0]=DBL_MAX`, `v[0]=1e308` and other positions `(0,1),(0,-1)` returned Numerical error with nonfinite final/frame coordinates. This is not reachable through the fixed grid/fixture CLI, but matters to the exported stateless API. The core owner fixed representability checks in `870683f833612f200934bbbd46a44c2de144b541`. The public API rejects such arithmetic while preserving exact-coincidence Close encounter at time zero and its allowed nonfinite energy diagnostics.
3. **Non-UTF-8 error output, low.** A POSIX argv byte string `b'--\\xff'` was copied into an error message, producing invalid UTF-8 rather than JSON. The CLI owner removed arbitrary bytes from the unknown-flag diagnostic in `c83f06eaeb102ee9af35da887f0d9e4bfb97bba8`. Independent raw-byte argv testing now receives exit 2, valid JSON stderr and no success stdout.
4. **Unlinked source/build provenance, medium.** The comparison tool originally hashed the current source and an arbitrary supplied binary independently, allowing a stale/external binary to be reported with current source identities. The parity owner fixed linkage in `74016dc7197158f31fa2c1e691e68d16437cd30a`: required builder metadata must match the actual binary, current native source hashes, accepted FP flags and consistent compiler/build identity before comparison executes. Missing/tampered/stale linkage rejects. This establishes recorded integrity, not attestation against a publisher able to forge all metadata.

The coordinator also found the initial parity harness demanded bitwise equality of nonzero trigonometric fixture velocities, despite the frozen contract's existing 1e-9 absolute-plus-relative policy. Its correction uses that predeclared bound and retains exact zero velocities for scan states; no numerical tolerance was relaxed after seeing output.

All implementation fixes remain owned by their original component agents. Independent regression probes are in `verification/native_reference_adversarial.py`.

## Reproduced acceptance

At final implementation head `4986033b861d1526062ae41efdd9147aa55e31cb`:

- `python3 -m unittest verification.native_reference_adversarial -v`: **5 passed**, compiling the real native sources and testing arithmetic overflow, valid-JSON error handling, build provenance rejection, direct-core bounds/state isolation and unchanged orbit-screen compatibility.
- `python3 -m unittest discover -s tests -p test_native_parity.py -v`: **9 passed**, including all 2,300 initial states on the smallest supported grid and the 22-case bounded native/JavaScript report.
- Actual native figure-eight raw record was passed to the unchanged JavaScript `Orbit.analyze`: detected three repeating cycles, period `5.713338304503539`, maximum normalized recurrence error approximately `0.0012983389503894438` within the unchanged 0.02 threshold. This is a nonzero-velocity comparison fixture and an orbit-candidate screen, not a rest-start search result or stability proof.
- Direct native core analytic/edge tests passed under AddressSanitizer and UndefinedBehaviorSanitizer. Hosted execution required `ASAN_OPTIONS=detect_leaks=0` because LeakSanitizer could not inspect `/proc` in this environment. Leak detection is not claimed as passed. The sanitizer-reviewed native sources are unchanged between `a550dd79906dfaaeb08f0a467ce1f63b99bac09e` and the final implementation head.
- `git diff --exit-code d5cf5342bad7c09d1dd3531de2af6076808e7a5d HEAD -- baseline workers services viewer`: clean. The accepted browser physics and production pipeline implementation are unchanged.
- `git diff --check`: passed.

No unresolved blocking code findings remain in this reviewed native-reference scope. The final publication tree, current base/head and hosted CI still require coordinator checks; any implementation change invalidates this exact-head conclusion.

## Acceptance limits

This validates a bounded native CPU reference, not broad native production enrollment. Long chaotic final-state discrepancies are reported rather than claimed bitwise identical. Actual Windows, physical heterogeneous machines, HIP compilation/execution, RX 7900 XTX throughput and rendered-browser acceptance remain separate gates. No mathematical permanent-stability proof, driver change, live deployment or production-backend replacement is established.

## Final direct-CLI addendum

After the first corrected review, the coordinator reproduced a command-line import defect: invoking `python3 scripts/compare_native.py` directly could not import `scripts.build_native`, even though module-import unit tests passed. The parity owner fixed script entry-point setup in `5c50b037` and added an actual subprocess regression. The independent verifier separately reproduced the old `ModuleNotFoundError` with `PYTHONPATH` removed and invocation from an unrelated temporary working directory.

At final reviewed head `239adb2697408173754bf2d9397b2f6929f554f9`:

- `python3 -m unittest verification.native_reference_adversarial -v`: **6 passed**, now including the real documented report command invoked by absolute script path from an unrelated working directory with no `PYTHONPATH`. Its 22-case report passes the fixed policy and verifies build linkage.
- `python3 -m unittest discover -s tests -p test_native_parity.py -v`: **10 passed**, including the owner's direct-CLI regression.
- The existing baseline, production workers, services and viewer remain byte-for-byte unchanged from accepted upstream `d5cf5342bad7c09d1dd3531de2af6076808e7a5d`.

All reported findings, including the direct-CLI failure, are resolved at this final implementation head. There are no unresolved blocking code findings in the isolated native-reference scope. Final source-tree publication mapping and current-head hosted CI remain coordinator merge checks.
