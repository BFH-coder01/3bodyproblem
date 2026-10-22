# Three-Body Lab agent instructions

Read the task assignment envelope and relevant design/roadmap before editing. Confirm task ID, owner, role, accepted base SHA, branch, permitted paths, dependencies and acceptance commands. If those are missing, continue read-only inspection and ask the coordinator for the missing dispatch information.

## Ownership

- Work only in your assigned worktree and task branch. Other machines have separate clones.
- Do not modify another task's worktree, shared Git configuration, main, release tags or protected settings.
- Shared contracts/build/CI files have a named owner. Propose cross-scope changes to the coordinator; do not quietly edit them.
- Development agents own implementation commits and handoffs. The coordinator alone merges accepted PRs after delegated authority and independent verification. The verifier reports evidence and does not self-approve changes it authored.
- A task instruction does not grant credentials, background execution, permission to bypass protections or release authority.

## Scientific behavior

- All search bodies start at rest. Compute every pair's gravity and update every body; exact symmetry may yield zero net acceleration.
- Preserve the accepted model/numeric version and units. Do not add mass merging, softening, initial velocity, altered boundaries, looser error limits or FP32 filtering as a performance shortcut.
- The current baseline stops at close encounters. Merging is a separate model decision with conservation/replay requirements.
- Escape means leaving the observation square. Show all escaped outcomes regardless of duration; show other outcomes automatically only when simulated time is >5 seconds.
- Call recurrence results orbit candidates. Do not claim proven permanent stability from a finite run.
- Never mark a CPU fallback, compile-only HIP test, skipped hardware check or guessed throughput as GPU success.

## Workflow

Run acceptance checks relevant to your change. Preserve exact commands, environment IDs and results. Do not invent test output. Keep artifacts and secrets outside Git. Use structured task/result data and argument arrays for executable calls.

Commit cohesive changes on your task branch and push/open a PR only when that scope is authorized. Include task/base/head SHAs, changed paths, evidence, test commands and unresolved findings in the handoff. Any new head invalidates prior exact-head verification. Do not force-push a shared branch, bypass a failed check, or merge main independently.

Read `docs/04-agent-and-git-model.md` for integration and `docs/06-coordination-authorization.md` for delegated authority. Task templates start planned; only a coordinator-approved ready assignment can dispatch implementation. Do not launch all roadmap tasks concurrently.
