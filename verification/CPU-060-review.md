# CPU-060 independent review

Reviewer: a separate Codex agent that authored no implementation component. This is independent model review evidence, not a distinct GitHub-actor approval. Review scope is the CPU reference increment, not mathematical stability proof, native parity or GPU acceptance.

Initial reviewed code head: `5c9840d1f15ae25d31b36e1ef915299da2fec414`.

## Initial evidence

- `python3 -m unittest discover -s tests -v`: 25 tests passed, including actual Node execution, concurrent local coordinator work, HTTP worker publication, restart and retained replay endpoints.
- `node tests/reference-pipeline.cjs`: passed.
- `node tests/viewer-model.cjs`: passed.
- `node baseline/tests/physics-scan.cjs`: passed.
- Read the frozen protocol, reference worker, Python supervisor, ledger, HTTP handlers, viewer model and client.

## Findings sent to owners

1. **Publication validation, medium:** a result with `outcome: []` or `{}` caused an uncaught TypeError at set membership rather than a structured 4xx rejection. An oversized but valid JSON integer such as `time: 10**1000` caused an uncaught OverflowError in float finiteness conversion. The HTTP handler did not convert these to protocol errors. Owner fix: `869e3c421d838c0c1d02616d385d64bffaf992b9`.
2. **Scientific metadata integrity, high:** a six-second bounded summary with `orbit.detected=true`, `cycles=3`, `period=100`, `tolerance=999`, and `maxNormalizedError=1` was accepted. These values cannot satisfy the baseline recurrence screen. Owner fix: the same ledger correction enforces baseline recurrence bounds.
3. **Distributed replay completeness, high:** after a playlist scan completed at a high ordinal, a later accepted eligible trial at a lower ordinal outside the currently visible page could be missed permanently. The refresh path reopened scanning without resetting its high ordinal cursor. Owner fix: `4708dc67559e7a589d5a4a4266fea68bb19e6559` restarts a completed scan when coverage has grown, while leaving active scans intact.

All findings were reproduced or traced to the actual control flow and sent to the coordinator and component owner before remediation. Implementation changes remain owned by those agents. Independent actual-reference/HTTP probes are in `verification/test_adversarial_publication.py`.

## Corrected code verification

Reviewed corrected integrated code head: `dd18d00c5caf8576187462a19b6eb5600f2d585c`.

- `python3 -m unittest discover -s tests -v`: **26 passed**.
- `python3 -m unittest discover -s verification -v`: **2 passed**. These use real Node output, actual HTTP requests and concurrent claim attempts. All malformed publications return structured HTTP 400 with zero accepted rows; the subsequent honest publication and identical retry preserve exactly one accepted trial. Eight concurrent claim attempts acquire three distinct task ranges, preserved after reopening the ledger.
- `node tests/reference-pipeline.cjs`: passed.
- `node tests/viewer-model.cjs`: passed, including late ordinal 100 discovered after a completed scan through ordinal 999, without resetting active scans or looping after coverage is complete.
- `node baseline/tests/physics-scan.cjs`: passed.
- `git diff --check`: passed.
- Static DOM cross-check: all literal JavaScript element references exist in the HTML; no duplicate HTML IDs.

All three reported code defects are resolved at this code head. No unresolved blocking code findings remain in the reviewed CPU scope. The reviewed source and the new verification files must still be tied to the exact publication tree/head, CI and current base before integration; this report does not authorize ignoring a later code change.

**UI rendering acceptance remains pending.** The coordinator reports that Chromium installation was blocked by its download path and the cloud browser could not reach the local server. Neither this verifier nor the coordinator claims an actual rendered-browser inspection. The viewer has passing pure-model tests and static control-flow/DOM review; those do not replace visual and interactive browser QA.

## Final code and decimal hardening addendum

Final reviewed implementation head: `ea2ae78c0c2423729a36e2819a1a9e52b06c94f9`.

The additional low-severity decimal parser edge is resolved: a 5,000-digit ordinal string previously reached Python's integer-string conversion limit and produced a structured server error rather than a client error. The owner now rejects oversize strings before conversion. Independently checked 5,000-digit and 17-digit strings, the value immediately above the JavaScript safe-integer maximum, the accepted maximum `9007199254740991`, and zero. The eight ledger/API regressions pass at this implementation head.

The two independent HTTP/concurrency probes also pass at this head, including the added 5,000-digit result ordinal mutation. It returns structured HTTP 400, preserves zero accepted rows, and leaves the honest result publishable once. All prior blocking findings remain resolved. Changes since the earlier reviewed code were inspected for this parser correction; the rendered-browser and actual GPU/second-machine acceptance limits remain unchanged.

Final publication must still preserve the reviewed implementation tree and receive passing CI; this addendum does not pre-approve later implementation edits.

## Limits

The source digest pins the checked-in numerical reference implementation; it does not attest execution by an untrusted machine. The HTTP API is intentionally limited to a trusted research LAN and lacks authentication/TLS termination. Actual Windows execution, a second physical machine, HIP kernels and RX 7900 XTX execution remain separate acceptance work. The browser baseline remains the physics reference; finite recurrence remains an orbit candidate rather than permanent-stability proof.
