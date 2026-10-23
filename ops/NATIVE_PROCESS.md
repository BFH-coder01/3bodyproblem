# Native reference agent wave

User confirmed cloud work may continue while the physical heterogeneous lab is unavailable, then requested proceeding. This wave implements and independently verifies an isolated native FP64 reference. The existing CPU pipeline and physical model remain unchanged.

| Task | Owner | Allowed paths | Acceptance |
| --- | --- | --- | --- |
| NAT-010 | Coordinator | contracts/, native/include/, scripts/build_native.py, docs/, CI, ops/, inventory | Frozen ABI, reproducible build, integrated evidence |
| NAT-020 | Core agent | native/core/threebody.cpp, native/tests/core_test.cpp | Stateless math/integration and meaningful C++ fixtures |
| NAT-030 | CLI agent | native/cli/main.cpp | Strict argv/JSON boundary, no dependencies |
| NAT-040 | Parity agent | tests/test_native_parity.py, scripts/compare_native.py | Real C++ versus JS tests and disagreement report |
| NAT-060 | Independent verifier | verification/native* | Exact-head adversarial review; findings returned to owners |

Each agent branches from the frozen contract commit in its own local worktree. Coordinator integrates and publishes one reviewed PR; completed component branches will not be retained on GitHub after acceptance. The handoff/evidence remains in the repository, avoiding the earlier redundant compare prompts. Native parity is distinct from full roadmap or GPU acceptance.


## Verified result

The native core and strict CLI are implemented. Parity covers all 2,300 initial states on the smallest grid, analytic forces and cancellation, known rest-start events, comparison-only periodic fixtures, strict argument handling and a 22-case cross-language sample with verified build provenance. Exact commands, counts and limits are in docs/12-native-validation.md and ops/evidence/NATIVE-PARITY.json. Owner commits and fixes are recorded in ops/native-handoffs.json.

The independent reviewer challenged overflow handling, raw-byte JSON diagnostics, binary/source provenance and the documented command entrypoint. Owners fixed each finding and the reviewer reran adversarial probes on corrected code. Native enrollment into the durable ledger is still a separate gate; this does not replace the JavaScript worker or upgrade a rig toolchain. No action is required from the user's Android device.
