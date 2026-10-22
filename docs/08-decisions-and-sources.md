# Decisions, assumptions and references

Prepared 23 October 2026, Australia/Brisbane. Product support changes; check the selected version and actual rig before installation.

## Proposed initial decisions

- Dedicated monorepo: `BFH-coder01/3bodyproblem`, supplied by the owner and observed as public. The bootstrap preserves its existing MIT license.
- Windows 11 native HIP or native Linux ROCm selected in P0 after inventory; no assumed driver update.
- C++17 FP64 reference/core and HIP backend; Python 3.11+ supervisor/coordinator; existing browser viewer adapted later.
- One coordinator owns main integration; task agents own branches; independent verification; Werner owns scientific exceptions and releases.
- Worktree per task locally; clone per remote machine; initial three implementation slots and one serialized GPU test slot.
- Current point-mass close-stop model is the migration baseline. Merger and FP32/WebGPU screening are optional separate decisions.
- Preserve default all-rest initial states, radius-grid enumeration, all escapes plus non-escaped durations >5 s in the viewer, and honest orbit-candidate terminology.
- Runtime computation is independent from animation. Summaries cover every trial; full replays can be generated from pinned IDs/builds.

## Open items before dispatch

Actual repository URL/visibility and account plan; author/reviewer/coordinator identities and permissions; rig OS and current AMD toolchain; available local/remote agent execution paths; scientific/model approval; CI provider and trusted GPU runner access; storage budget and evidence retention; whether the first release needs a merger model. None should be silently assumed to have been configured by this document.

## Official sources

1. Git worktree documentation: https://git-scm.com/docs/git-worktree — separate working trees and shared metadata; supports the local worktree design.
2. GitHub protected branches: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches — checks, stale review rules and availability by repository plan/visibility.
3. GitHub PR reviews: https://docs.github.com/en/pull-requests/reference/pull-request-reviews — review behavior; a latest-push approval policy needs another authorized actor.
4. Official OpenAI documentation, Worktrees: https://learn.chatgpt.com/docs/environments/git-worktrees — parallel task isolation; worktrees run on the project computer/remote environment, not the phone; managed worktrees can start detached.
5. Official OpenAI documentation, AGENTS.md: https://learn.chatgpt.com/docs/agent-configuration/agents-md — root/nested durable instructions and precedence.
6. AMD Windows HIP requirements: https://rocm.docs.amd.com/projects/install-on-windows/en/develop/reference/system-requirements.html — RX 7900 XTX, gfx1100, HIP runtime/SDK listed; select a released version for the actual build.
7. AMD Radeon Linux support: https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/native_linux/native_linux_compatibility.html — supported GPU/environment matrices; verify selected tuple locally.
8. W3C WGSL specification: https://www.w3.org/TR/WGSL/ — standard shader numeric types; native FP64 is absent from the baseline WebGPU route described here.
9. Three-body equations/conserved quantities: https://www.scholarpedia.org/article/Three_body — momentum, angular momentum and distinctions relevant to the model.
10. Chenciner/Montgomery figure-eight reference: https://arxiv.org/abs/math/0011268 — periodic equal-mass orbit; its nonzero starting velocities make it a comparison fixture, not an all-rest discovery.

Architecture, task sizes, authority levels and phase gates in this pack are proposed engineering decisions. Vendor documentation supports compatibility and tool behavior, not a measured speedup for this solver. No 7900 XTX benchmark, remote deployment or permanent-stability proof is claimed.
