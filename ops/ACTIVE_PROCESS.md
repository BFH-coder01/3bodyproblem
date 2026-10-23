# Active agent process

Owner request (23 October 2026, Brisbane): coordinator takes control and uses agents of itself to develop independent stateless components orchestrated as a pipeline. This delegates routine task branching, implementation, verification and integration merges for the requested codebase. Scientific model changes, driver changes, public deployment and release tagging remain outside this increment. Agent sessions run during the active task; no unattended background service is implied.

Accepted upstream base: `d2ec4b41a544dede14a94db08b5741c17d32ffe2`.

First increment: CPU reference vertical slice. Preserve point-close-stop/rest-start behavior. The CPU protocol does not depend on an unverified rig tuple; it is a precursor to the native/HIP roadmap, not completion of the GPU gates. Existing TBL-001 rig acceptance and native parity tasks remain pending.

| Task | Owner | Scope | Dependencies | Acceptance |
| --- | --- | --- | --- | --- |
| CPU-010 | Coordinator | contracts/, ops/, workers/cpu_worker.py, root docs/CI/integration | Merged foundation | Freeze pipeline-v1.md, orchestration and actual end-to-end test |
| CPU-020 | Reference agent | workers/reference-cli.cjs, tests/reference-pipeline.cjs | Frozen CPU-010 contract | Node protocol/stateless and baseline parity tests |
| CPU-030 | Ledger agent | services/, tests/test_pipeline_ledger.py | Frozen CPU-010 contract | Transaction/restart/lease/HTTP validation tests |
| CPU-040 | Viewer agent | viewer/, tests/viewer* | Frozen CPU-010 contract | Real API table, replay and filters |
| CPU-060 | Independent verifier | verification/, review fixes only as assigned | Integrated CPU-020/030/040 head | Reproduce acceptance, adversarial faults, exact-head review |

Each implementation agent gets a distinct Git worktree and branch at the frozen contract commit. Coordinator alone changes shared contracts/CI and serializes integration. Agent instructions include the resolved commit, permitted paths, commands and handoff evidence. Task agents commit locally; coordinator publishes branches/PRs to GitHub. The verifier does not approve code it authored. Findings return to the component owner.


## First increment outcome

Reference, scheduler, viewer and platform components are implemented. The independent verifier reproduced all reported defects and rechecked the owners' fixes; independent adversarial probes are enforced in CI. Integration and component publication heads are recorded in `ops/agent-handoffs.json`; the integration PR is the acceptance/merge record.

The 60-trial local/HTTP integration and 1,000-trial four-process campaign reconcile complete unique coverage. The replay viewer is code-complete with pure-model/static checks; rendered-browser acceptance remains pending due the hosted environment limitation. Runtime data and databases stay outside Git.

Next dispatch: run `python scripts/rig_inventory.py --out data/rig-inventory.json` on the actual 7900 XTX rig, record the chosen tuple, then implement native parity and the smallest GPU smoke test as separate workspaces. The CPU reference remains usable while those gates are pending. No native/GPU task is labelled passed from this hosted CPU run.

Agent sessions are bounded to active coordinator work. Future sessions resume by reading this file, the task handoffs, current main and verification evidence; no permanently running background agent was installed on the user's computers.


## Cloud native reference wave

Following the user's instruction to defer physical lab testing and proceed in cloud capacity, the coordinator dispatched the isolated native FP64 wave documented in ops/NATIVE_PROCESS.md. Its source, tests, independent findings and source/build-linked parity evidence are recorded in the repository. The accepted JavaScript pipeline is unchanged. Native worker enrollment, lab compatibility and GPU execution remain separate gates. Resume from the latest merged PR, docs/11-native-reference.md and ops/native-handoffs.json.
