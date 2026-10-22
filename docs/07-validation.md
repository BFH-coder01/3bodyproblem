# Validation and completion gates

## What has actually been tested for this pack

The workspace utility is exercised against disposable real Git repositories with a local identity and temporary directories. Tests cover plan-only behavior, exact base commit capture, named branch/worktree creation, paths with spaces, refusal of an unready task, refusal of a role mismatch, refusal of a dirty root clone, and preservation of an existing workspace/branch. No test contacts GitHub or installs/runs HIP.

The application tests and GPU acceptance tests below are implementation requirements, not claimed execution results. The current browser baseline previously demonstrated rest-start forces, enumeration order, periodic-reference screening and escaped/display-duration rules; migrate and pin these as fixtures before changing their engine.

## Required scientific fixtures

| Fixture | Purpose | Required observation |
| --- | --- | --- |
| Unequal-separation asymmetric rest start | Every body feels both others | Three independently computed accelerations; all bodies move; net pair force cancels within a defined tolerance. |
| Symmetric collinear rest start | Detect false fixed-body accusations | Middle acceleration can be zero through cancellation while both outer bodies move. |
| Pairwise distance scaling | Inverse-square units | One source at 1 m gives μ; at 2 m gives μ/4 in the same direction. |
| Known figure-eight comparison | Numerical recurrence reference | Nonzero-velocity reference is labelled comparison-only; period/diagnostics agree under refinement. |
| Close encounter | Singularity handling | Separate stopping code; no silently merged or stationary mass. |
| All-rest escaped case | Escape classification | Square crossing captured; selected for replay even when elapsed time ≤5 s. Existing example: radius 2 m, zero-based ordinal 57, about 4.77 s under the baseline settings. |
| Duration boundary | Viewer policy | Escaped always selected; non-escaped 5 s excluded, >5 s included; wall-clock/replay speed does not alter selection. |
| Perturbed candidates | Evidence strength | Longer/refined trajectories and bounded perturbation behavior reported without proof-of-stability language. |

## Software and distribution gates

1. Exact rank/unrank agreement over all small grids and sampled extreme ordinals, including first/last triples and row/column boundaries.
2. CPU single/multiprocess and two-machine runs reconcile expected unique trial IDs with accepted summaries; no gap is hidden by duplicate counts.
3. Kill a worker mid-batch; expire/reassign lease; submit a late old-epoch result; replay duplicate chunks; restart coordinator. Accepted coverage is still correct.
4. Interrupt artifact upload and restart replay generation. Metadata never advertises missing or unchecked bytes as complete evidence.
5. Disconnect the viewer, change playback speed and fill its queue. Numerical throughput continues and selected replay records remain discoverable.
6. Simulate disk full/database failure/network partitions. Workers spool bounded data, stop/retry by policy, and expose evidence gaps rather than silently dropping trials.
7. Authentication/capability mismatch, malformed ranges and manifest hash mismatch are rejected without arbitrary command execution.

## 7900 XTX proof and performance record

First hardware experiment: a single tiny HIP FP64 trial with detected `gfx1100` (or explicitly documented actual target), pinned OS/driver/runtime/compiler, build SHA, input manifest hash, stdout/stderr and exit code. Verify work executed on the GPU with the agreed device instrumentation. Compile-only or a CPU fallback is not a pass.

Then use repeated representative workloads at batch sizes such as 1,024, 4,096, 16,384 and 65,536, subject to measured memory/kernel-duration limits. These are proposed trial counts, not promised simultaneous residency or performance. Record cold start and steady-state wall time, unique accepted trials/s, step counts, active-trial divergence, peak VRAM, CPU/I/O overhead, power/temperature if available, and disagreement/uncertainty rates. Reserve the GPU so a resident local model does not confound the measurements.

Compare a host FP64 build, multiprocess CPU execution and GPU FP64 at the same semantics. Report numerical failure and unresolved rates alongside speed. Avoid benchmark suites containing only the first adjacent top-row configurations. A slower but valid backend remains useful; never alter stopping criteria solely to improve headline throughput.

## Completion means

A phase is complete only when its acceptance evidence is attached to the exact accepted commit and independently checked. A full-campaign claim needs complete reconciled coverage of its declared grid and model, with unresolved/rejected work accounted for. Finding a numerical recurrence is not the same as proving an equilibrium orbit or stability.

Every release evidence pack records input space, physics/numerical versions, build identities, environments, diagnostic limits, classification counts, unresolved cases, verifier reports and reproducible commands. Keep data artifacts outside Git and include content hashes in the release metadata.
