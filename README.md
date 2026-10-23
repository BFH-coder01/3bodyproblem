# Three-Body Lab — distributed simulation pipeline

Prepared for Werner van Huffel · 23 October 2026 · Australia/Brisbane.

**Recommendation:** one coordinator, protected `main`, one local clone per machine, and one isolated Git worktree per active development task. Agents own task branches; the coordinator owns integration; Werner owns scientific scope and releases.

This repository includes a working CPU pipeline: stateless trial functions, a durable lease/result coordinator, local parallel workers, HTTP workers for a trusted LAN, and a separate replay viewer. The original browser solver remains unchanged as the reference. An isolated C++17 FP64 reference and cross-language parity suite are also available; native pipeline enrollment, HIP acceleration and actual RX 7900 XTX acceptance remain subsequent gates.

## Run the pipeline

Install Node 18+ and Python 3.11+, then run from this repository root:

```bash
python3 -m services.pipeline init --db data/demo.sqlite --radius 2 --duration 6 --count 60 --chunk-size 5
python3 -m services.pipeline run --db data/demo.sqlite --workers 2
python3 -m services.pipeline serve --db data/demo.sqlite --port 8765
```

Open http://127.0.0.1:8765. On Windows, use `python` if that is your Python command. [The runbook](docs/10-cpu-pipeline-runbook.md) covers multiple machines, recovery and function boundaries. [Native reference validation](docs/11-native-reference.md) explains the optional C++ build and provenance-checked comparisons. [Rig readiness](docs/09-rig-readiness.md) collects read-only environment evidence. [The active process](ops/ACTIVE_PROCESS.md) records agent ownership and integration authority.

## Read in this order

1. [Architecture](docs/01-architecture.md) — runtime and development control planes.
2. [Design](docs/02-design.md) — contracts, scheduler, numerical behavior and evidence.
3. [Roadmap](docs/03-roadmap.md) — dependency gates and workspace assignments.
4. [Agent and Git model](docs/04-agent-and-git-model.md) — ownership and merge procedure.
5. [Rig and workspace runbook](docs/05-rig-and-workspaces.md) — Windows/Linux setup commands.
6. [Coordination authorization](docs/06-coordination-authorization.md) — how to delegate branching and merging.
7. [Validation](docs/07-validation.md) — acceptance evidence and hardware benchmarks.
8. [Decisions and sources](docs/08-decisions-and-sources.md).

The root `AGENTS.md` governs agent work in this repository. Agent prompts, handoff templates, task manifests, a proposed ownership map, CI guidance and workspace scripts are included. They are project instructions, not an installed agent skill.

## Repository and machine paths

Repository: [BFH-coder01/3bodyproblem](https://github.com/BFH-coder01/3bodyproblem), created by the owner and observed as public. Its existing MIT license is preserved.

Windows: `D:\Development\ThreeBodyLab\repo`, with sibling `worktrees`, `data`, and `artifacts` directories. Linux: `~/Development/ThreeBodyLab/repo`, with the same siblings. Every remote machine uses its own clone and its own local worktrees.

The existing browser implementation is the migration baseline, observed at commit `945f1aeca3f3e11b516169ae9361bbeaaad11fdf`. Its runtime source and tests are imported without edits under `baseline/`, following owner approval to commit and push into this public repository. See [baseline provenance and run instructions](baseline/README.md).

## What can be used now

Python 3.11+ and Git are the only dependencies for the workspace helper:

```bash
python scripts/workspaces.py plan --repo . --task TBL-010 --agent contracts --role contracts --base main
python -m unittest discover -s tests -v
```

`plan` changes nothing. `create` creates a named task branch and worktree from a resolved commit and writes a local task envelope. Neither command pushes, opens a PR, merges, changes GitHub permissions, starts an agent, or installs software. Read the runbook before creating worktrees.

TBL-000 was merged as PR #1. The CPU reference increment uses the frozen `contracts/pipeline-v1.md` interface and independent CPU task assignments in `ops/ACTIVE_PROCESS.md`. The native/HIP roadmap retains its separate rig, contract and parity gates; the draft native schemas are not silently accepted by this CPU implementation.

## Check this foundation

```bash
python3 -m unittest discover -s tests -v
node baseline/tests/physics-scan.cjs
node tests/reference-pipeline.cjs
node tests/viewer-model.cjs
python3 scripts/validate_bootstrap.py
```

The `bootstrap` GitHub Actions workflow runs Python unit/process/HTTP tests, browser-reference physics tests, stateless protocol tests, viewer-model tests and the tracked-source inventory check. See `VALIDATION_REPORT.md` for evidence and limitations. The coordinator uses isolated task worktrees and independent model verification during active sessions; this does not create a permanently running unattended development service. Runtime workers execute only the pinned reference implementation. No GPU run, driver change, live Site deployment or mathematical proof of stability is implied.
