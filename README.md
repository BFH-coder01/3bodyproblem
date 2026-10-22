# Three-Body Lab — distributed development pack

Prepared for Werner van Huffel · 23 October 2026 · Australia/Brisbane.

**Recommendation:** one coordinator, protected `main`, one local clone per machine, and one isolated Git worktree per active development task. Agents own task branches; the coordinator owns integration; Werner owns scientific scope and releases.

This repository contains the browser simulator baseline, architecture, design, roadmap and tested workspace-tooling starter. It does not implement the distributed solver, configure GitHub, install AMD drivers, connect to your rig, or start autonomous agents.

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

TBL-000 is prepared for review; other task statuses are `planned`; a roadmap-ready task is not an instruction to dispatch it before its dependencies are accepted. Sample schemas are proposed starting contracts and must pass the P1 contract gate before implementation agents depend on them.

## Check this foundation

```bash
python3 -m unittest discover -s tests -v
node baseline/tests/physics-scan.cjs
python3 scripts/validate_bootstrap.py
```

The `bootstrap` GitHub Actions workflow runs the workspace, browser physics/replay and inventory checks. GPU checks and protected-branch settings have not been configured. TBL-000 includes the approved browser source import; independent verification and acceptance remain pending. The following gates are rig inventory (TBL-001), scientific model decision (TBL-002), and contracts (TBL-010). No remote agent has been launched and routine main-merge authority has not been delegated.
