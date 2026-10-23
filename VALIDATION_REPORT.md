# CPU reference pipeline validation

Executed 23 October 2026 in the hosted Linux workspace. The unchanged browser source remains the numerical reference. Implementation was split across isolated reference, ledger, viewer and platform branches; a separate agent independently reviewed integration and returned findings to the original owners.

- Functional code head: `ea2ae78c0c2423729a36e2819a1a9e52b06c94f9`.
- `python3 -m unittest discover -s tests -v`: 26 passed, including actual Node subprocesses, two-process orchestration, loopback HTTP worker publication, restart, fencing, replay retrieval, inventory tooling and worktree safety.
- `python3 -m unittest discover -s verification -v`: 2 independent actual-reference/HTTP/concurrent-claim probes passed.
- `node tests/reference-pipeline.cjs`: passed stateless parity, input faults, finite output, bounded line handling and replay policy.
- `node tests/viewer-model.cjs`: passed filtering, interpolation, large test labels and late out-of-order replay discovery.
- `node baseline/tests/physics-scan.cjs`: unchanged baseline tests passed.
- `python3 scripts/validate_bootstrap.py`: tracked inventory hashes and task graph checked after all intended files were staged.
- `python3 scripts/rig_inventory.py --out ...`: ran on the hosted CPU environment; explicitly no GPU execution claim.
- `git diff --check`: passed.

A real 1,000-trial campaign (radius 2 m, 6 simulated seconds, ordinals [0,1000), chunks of 16, four worker processes) finished with exactly 1,000 unique accepted trial IDs, no missing ordinals and no duplicates: 843 close encounters, 138 bounded observations and 19 escapes. It retained 193 replays, including six escapes shorter than five seconds. This is a bounded integration test and does not establish permanent stability or an exhaustive search.

See ops/evidence/CPU-PIPELINE.json for commands and results, verification/CPU-060-review.md for independent findings/remediation, and ops/agent-handoffs.json for local/remote component head mappings. GitHub CI logs provide hosted evidence at the published PR head. The GitHub connector creates publication commits from verified source trees because native Git push has no credentials in this environment; metadata records both local and remote SHAs rather than pretending they are identical.

Independent review found and fixed malformed-result exceptions, impossible orbit metadata, a replay playlist that missed late lower ordinals, and oversized decimal input handling. The verifier did not author implementation fixes or impersonate a second GitHub reviewer.

Limits: rendered-browser inspection remains pending (Chromium download failed; cloud browser cannot reach the local server). The viewer has functional model tests and static DOM/control-flow review. Actual Windows, a second physical machine, native FP64 parity, HIP and the RX 7900 XTX remain separate acceptance gates. The API is for a trusted LAN and lacks authentication/TLS termination. No driver changes, branch protection changes, release tags, public deployment, mass merging or physical-model changes were made.
