# Delegating branch and merge coordination

## Recommended allocation

Werner is the project/science owner and release authority. One designated coordinator handles task dispatch, branch naming, accepted base commits, dependency order, review routing, integration checks and routine merges. Each development agent commits/pushes its own branch and provides evidence. An independent verifier challenges the implementation; it does not own main.

This reduces repeated manual merge administration without letting every agent merge concurrently. The coordinator is a role, not necessarily a permanently running service or a particular model. ChatGPT can fill that role while an authorized session has the relevant connected repository tools or access to an authenticated local checkout. It cannot silently access `D:\` on your rig from this hosted chat. A local Codex session or an explicitly provisioned remote execution path is needed to run commands there.

## Authority levels

| Level | Scope | Current status / activation |
| --- | --- | --- |
| A0 | Read sources, draft plans, create this pack and test its workspace helper in disposable local repositories. | This request authorizes this planning work. |
| A1 | Create task branches/worktrees, commit, push assigned branches, prepare PRs and run approved development checks in one named repository. | Activate with an explicit repository-specific instruction and actual access. |
| A2 | Coordinate and merge routine in-scope PRs to main after all stated gates, without asking again for each merge. | Recommended after baseline, access and branch controls are verified; activate explicitly. |
| A3 | Physics model changes, mass-merger policy, protocol breaks, driver/runtime changes, protection changes, release tags, live deployment or a long production campaign. | Reserved to Werner unless separately delegated for a named concrete action. |

Authority levels are proposed project governance, not a change to platform tool permissions. Tool availability and account permissions still apply. Ordinary bug fixes remain A1/A2 when they preserve accepted behavior and pass the gates. Do not turn every routine implementation choice into a new approval request.

## One-time activation steps

1. The owner supplied https://github.com/BFH-coder01/3bodyproblem, approved publishing the browser baseline, and directed the coordinator to merge PR #1. On 23 October 2026 the owner then requested coordinator control and parallel agents to develop the stateless pipeline. Routine in-scope implementation, verification and integration are delegated for this increment; see `ops/ACTIVE_PROCESS.md`. This does not delegate model changes, rig driver changes, protection bypasses or public deployment.
2. Connect the appropriate GitHub account/app with access to that repository, or open the authenticated checkout in the local coding session. Repository-scoped content/PR/check-reading capabilities are sufficient for routine work; administration rights are only needed for the human's initial protections setup. Avoid granting routine agents organization administration.
3. Set protections/rules in GitHub if your plan supports them. Confirm required checks exist, stale reviews are invalidated, no bypass is being used, and review actors can satisfy the chosen policy.
4. Place `AGENTS.md`, the agreed Git model and templates in the accepted baseline. Name the coordinator and independent reviewer identities. Record which real GitHub actor creates PRs, approves reviews and merges.
5. Start at A1 for the bootstrap and contract gate. Activate A2 when its gates are concretely testable. A review by another model using the same GitHub identity is useful evidence but may not satisfy GitHub's required distinct-actor approval rule.
6. Dispatch ready tasks with exact base SHAs and scopes. Give each agent a worktree and the relevant task/agent/handoff files. Limit simultaneous write owners per shared component.
7. Revoke or narrow the delegation by an explicit instruction and update the coordination ledger. Stop issuing new work before transferring coordinator ownership.

Do not paste PATs, passwords, API keys or SSH private keys into prompts. Do not use repository-wide write permission as if it were a token restricted to one branch. Never satisfy a review gate by having the author impersonate another reviewer.

## Suggested A1 activation instruction

> For repository [ACTUAL OWNER/REPO URL], act as the development coordinator under the accepted Three-Body Lab plan. You may create task branches and local worktrees, dispatch ready tasks to named agents, commit and push in-scope development changes, open/update pull requests, run the agreed checks, and prepare integration evidence. Each implementation agent owns its task branch. Leave main merges for my approval until I activate A2. Keep a durable record of task IDs, base/head SHAs, findings and next actions. Do not change the accepted physics, toolchain, protection rules, release tags or live deployment without separate authorization.

## Suggested A2 activation instruction

> For repository [ACTUAL OWNER/REPO URL], I authorize you as the sole integration coordinator to merge routine in-scope task PRs into main without asking me for each merge, provided the accepted task dependencies, independent verification, required checks and branch protections pass on the current head and base. Invalidate evidence after any relevant SHA change; serialize merges; never bypass protections, force-push shared branches or self-certify independent review. Agents may push only their assigned task branches and must not merge main. Keep physics/model changes, protocol breaks, GPU driver/runtime changes, protection changes, release tags, live deployment and long production campaigns for my separate approval. Record every merge and its evidence, and stop dependent merges on a regression.

These are ready-to-adapt instructions, not evidence that A1/A2 has already been activated. Naming a coordinator does not create a background process. If a required check, distinct reviewer or tool capability is unavailable, prepare the complete PR/evidence and report that specific remaining gate; do not claim a merge occurred.

## What you should handle yourself

Initially: repository/account access, scientific assumptions, choice of Windows versus Linux toolchain, and the first environment change. Subsequently: architectural exceptions and release approval. Routine branch creation, dependency tracking, conflict triage, evidence collation and authorized merges are appropriate coordinator work.
