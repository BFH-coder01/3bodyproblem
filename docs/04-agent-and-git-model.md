# Agent responsibilities and Git model

## Decision rights

| Action | Task agent | Independent verifier | Coordinator | Werner |
| --- | --- | --- | --- | --- |
| Define objectives/model change | Propose | Challenge/test | Record ADR | Approve |
| Assign task/base/scope | Acknowledge | Read | Own | Override priorities |
| Create branch/worktree | Via agreed helper | Detached verification worktree | Assign/create | Optional |
| Commit/push task branch | Own | Findings branch only | Routine administration | Optional |
| Approve readiness | Provide evidence | Verify independently | Check all gates | Required for reserved changes |
| Merge PR into main | No | No | Yes, after explicit delegation and gates | Can retain or revoke authority |
| Force push/delete main/bypass protections | No | No | No | Separate exceptional action only |
| Install/update drivers or GPU runtime | Propose | Record effects | Prepare exact change | Approve |
| Release tag/live deployment/long campaign | Propose | Evidence | Prepare | Approve |

One logical coordinator is active at a time. A replacement coordinator acquires the coordination lease and reads the persisted ledger before acting. Coordination state is not just chat memory. Different LLM providers can fill task roles using the same contracts, branch rules and handoff format.

## Branch policy

Use protected `main` plus short task branches, for example `agent/gpu/tbl-070-hip-smoke` or `agent/scheduler/tbl-030-leases`. Do not add a permanent `develop` branch initially. A temporary integration worktree is disposable, while its checks and result SHA are recorded.

Task branches start at an accepted commit, not another agent's unreviewed moving head. If a task needs an unmerged dependency, coordinator records the exact dependency SHA and the PR remains blocked until the dependency is accepted and the task is updated/retested.

The baseline branch must be clean when creating a new task workspace. Main is not a scratch area. Agents may commit and push their own assigned branches and open draft PRs when authorized. They do not merge other branches, update shared dependency locks, alter protected configuration, edit scientific fixtures outside scope, or publish releases independently.

Worktrees on one machine share Git metadata and configuration. They isolate files and indexes, not the operating system or credentials. Avoid concurrent repo-wide maintenance and global Git config changes. Remote machines use separate clones; never share a writable `.git` directory over a network filesystem.

## Handoff and independent verification

A PR description must include task ID, frozen base SHA, final head SHA, changed paths, tests and exact commands, environment/build IDs, evidence paths/hashes, compatibility changes, and unresolved findings. Use `templates/handoffs/implementation.md`.

The verifier checks out the exact head in a detached worktree, independently runs the specified acceptance tests and reviews scientific assumptions. It reports pass, fail or blocked with evidence. If it changes source to fix a finding, the resulting head needs another verification pass; writing a test report is not self-approval.

An agent review is an engineering artifact. GitHub approval requirements depend on real actor identities and repository settings. Multiple agents authenticated as the same user are not independent GitHub reviewers. If a required approval cannot be supplied by a distinct permitted reviewer/app, the coordinator must leave the PR pending for Werner rather than fake an approval or bypass protection.

## Merge procedure

1. Coordinator confirms the task is authorized, paths are in scope, and required upstream tasks are accepted.
2. Fetch `origin/main` and the PR branch. Record base SHA A and PR head SHA B. Freeze the PR head during verification by agreement; any new push invalidates stale evidence.
3. Create a clean detached integration worktree at A. Merge B there with `--no-ff --no-commit`, inspect conflicts, then create an integration test commit M locally. Never push M directly to main.
4. Run the required integration suite against M; record A, B, M, toolchain, commands, results and artifact digests. Treat skipped GPU tests as missing hardware evidence, not GPU success.
5. Use the hosting provider's merge queue if supported, or serialize coordinator merges with strict up-to-date checks. If A or B changes, rebuild and revalidate the integration candidate. A PR-head SHA guard alone does not guard against a changing base.
6. Merge through the PR API with the expected head SHA after all protections pass. Prefer a merge commit for clear task lineage; keep task commits cohesive. If the repository chooses squash instead, record B and verification evidence in the PR and resulting commit.
7. Fetch the actual new main commit, run required post-merge smoke checks, record it in the task ledger, and mark acceptance separately from merge.
8. On regression, prepare a revert PR. Do not reset or rewrite shared main. Worktree cleanup occurs only after the branch is pushed, evidence is preserved, and no uncommitted changes remain.

Agents should update a pushed task branch with a merge from accepted main rather than a force-push rebase. Conflict resolution stays in the task owner's branch or a coordinator-owned fix branch and is reviewed/tested anew. The coordinator may resolve a routine conflict only within the delegated scope; scientific or contract ambiguity returns to the decision owner.

## Required protections and checks

Configure PR-only changes to main, block force pushes/deletion, dismiss stale approvals where supported, require discussion resolution and unique named checks. Set expected status-check sources when available. Verify plan/visibility support for private repositories before relying on these settings.

Proposed checks: `contracts`, `reference-fixtures`, `enumeration-coverage`, `lease-recovery`, `host-build-linux`, `host-build-windows`, and the relevant `hip-smoke`/`hip-parity` gates for GPU changes. Add each required check only after its actual workflow exists and runs on applicable PRs. A placeholder `echo passed` is not a gate. Never rename a required job without updating protection configuration in a controlled change.

A shared GitHub identity with broad write access cannot be made into a hard per-agent path security boundary by a task document. Use repository-scoped credentials, separate service identities where available, protected main, and CI; treat path ownership as a workflow rule with an audited scope check.
