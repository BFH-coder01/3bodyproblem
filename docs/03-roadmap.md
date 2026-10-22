# Roadmap and workspace allocation

Phases are acceptance gates rather than promised dates. Hardware throughput, repository access, OS/toolchain and the collision model are not yet established on the rig. Start with three implementation slots, one verification slot and one coordinator; a slot is a task worktree plus an agent session, not a permanent branch.

| Phase | Task | Work package / owner | Dependencies | Acceptance evidence |
| --- | --- | --- | --- | --- |
| P0 | TBL-000 | Foundation / coordinator | Repository URL and authority agreed | Import existing Site baseline with provenance; preserve source commit; README, AGENTS and CI bootstrap committed. No live Site changes. |
| P0 | TBL-001 | Rig inventory / platform agent | TBL-000 | Read-only OS/GPU/driver/compiler/RAM/disk inventory; chosen Windows-HIP or Linux-ROCm tuple; one approved runtime path; no unsolicited driver upgrade. |
| P0 | TBL-002 | Model decision / Werner + numerical lead | TBL-000 | ADR fixes rest starts, radius semantics, μ, boundary and close-stop baseline; merger remains separate unless explicitly selected. |
| P1 | TBL-010 | Contracts and fixtures / contracts agent | TBL-001, TBL-002 | Manifest, task/result/replay schema versions; fixture IDs; precision/event tolerances; schema ownership approved. |
| P2 | TBL-020 | Headless reference / numerical agent | TBL-010 | Native FP64 CLI agrees with JS baseline within documented acceptance bounds; host tests and deterministic enumeration pass. |
| P2 | TBL-030 | Ledger and leases / scheduler agent | TBL-010 | Durable local coordinator; expiry, duplicate, stale-epoch, partial upload and restart tests pass. Uses a fake worker first. |
| P2 | TBL-040 | Viewer adapter / viewer agent | TBL-010 | Reads fixture/API replay stream; computes independently from animation; shows all escapes plus other durations >5 s. No live deployment yet. |
| P3 | TBL-050 | CPU worker supervisor / worker agent | TBL-020, TBL-030 | Local multiprocess workers finish a known range with no accepted gaps/duplicates, then a second machine joins. |
| P3 | TBL-060 | Verification service / independent verifier | TBL-020, TBL-030 | Candidate rechecks and uncertain-event queue; evidence links include exact source builds/inputs. |
| P4 | TBL-070 | HIP smoke and FP64 core / GPU agent | TBL-001, TBL-020 | 7900 XTX executes a tiny GPU-backed case; pinned logs and detected architecture; CPU/GPU diagnostics match on fixtures. |
| P4 | TBL-080 | GPU batching / GPU agent | TBL-050, TBL-060, TBL-070 | Bounded dispatches, active trial compaction and interruption recovery; measured throughput/VRAM and numerical agreement across batch sizes. |
| P5 | TBL-090 | Multi-machine integration / coordinator + verifier | TBL-040, TBL-050, TBL-060, TBL-080 | 100,000 mixed representative trials, worker termination and coordinator restart, reconciled coverage, replay backlog independent of compute. |
| P6 | TBL-100 | Pilot release / coordinator; Werner approves | TBL-090 | Signed-off evidence pack, rollback/runbook, immutable build tag, completed release checklist, explicit deployment decision. |
| Optional | TBL-110 | Finite-body merger model / numerical + GPU agents | Approved merger ADR and P3 baseline | Conservation including spin/energy accounting, contact resolution, new schemas, distinct three-body/binary/collapse labels. |
| Optional | TBL-120 | WebGPU or FP32 participation / GPU agent | P5 and approved precision policy | Quantified uncertainty, cross-device tests, rejected-case policy; no unsupported exhaustive claim. |

## Work waves

**Wave 0:** coordinator prepares TBL-000; inventory and model decision follow. This is the only point where broad shared-root changes are expected.

**Wave 1:** one contracts agent implements TBL-010; numerical and scheduler agents review the proposed interfaces without editing the same files. Coordinator freezes contracts at a commit and publishes task packets.

**Wave 2:** TBL-020, TBL-030 and TBL-040 can run independently in three worktrees. A verifier reviews completed heads; the coordinator serializes merges. Shared build/CI/schema changes return to their owner.

**Wave 3:** CPU integration and verification proceed while the GPU agent executes the smallest hardware smoke test. GPU-related commands use a single exclusive rig slot.

**Wave 4:** integrate HIP batching and representative multi-machine workloads. A performance failure can leave a valid CPU release path; it must not be disguised by dropping long-running or numerically difficult trials.

## Task lifecycle

`planned → ready → claimed → implementing → review → verification → merge-ready → merged → accepted`.

Blocked work has an explicit reason, dependency and next action. Only the coordinator sets `ready`, assigns a unique owner and accepted base SHA, and transitions to `merged`. Review evidence names the exact PR head. Verifier findings do not become resolved merely because a later agent says tests pass.

Task manifests in `ops/tasks/` are starter definitions, initially planned. Do not launch every phase concurrently. Create a new branch/worktree for the next task rather than indefinitely reusing a role's old branch.

## Pilot scale and evidence

First run 10 trials, then 1,000, then 100,000 representative trials only after preceding gates pass. Include geometries from distant ordinal ranges, close encounters, long survivors, escape events, numerical failures and threshold cases. The first adjacent top-row triples alone are a biased benchmark. No billion-trial campaign starts before coverage reconciliation and restart/replay tests pass.
