# Implementation agent task prompt

You own TASK_ID in WORKTREE_PATH on BRANCH, based at BASE_SHA. Read the coordinator's ASSIGNMENT_ENVELOPE_PATH, AGENTS.md and relevant design documents. Confirm permitted paths and dependencies before writing. Implement only this task and its acceptance criteria. Report a shared-interface dependency instead of editing another owner's paths.

Run the relevant checks, record commands/environment/results, commit cohesive changes and return the implementation handoff with final head SHA. Push your assigned branch/open a draft PR only if that scope is authorized. Do not merge main, change the scientific model or GPU environment, modify protection settings, or publish a release. Treat missing hardware checks as blocked evidence.
