# Rig and workspace runbook

## What is set up by this pack

The pack contains tested workspace tooling and ready-to-adapt task/agent templates. It has not changed the Windows rig, installed a HIP toolchain, created a GitHub repository, provisioned remote agents, or altered the published simulation. Run the following steps on the intended development host after the repository decision and authorization.

## 1. Establish the repository

Repository: `BFH-coder01/3bodyproblem`, created by the owner and observed as public. Verify and configure the desired protections separately; this bootstrap does not change repository settings.

Extract the pack into the intended new repo directory. Preserve the project's `.gitignore` and root `AGENTS.md` when importing this scaffold into an existing repository; merge instructions deliberately rather than overwriting them. The helper does not clone or initialize a repository automatically.

PowerShell example, after you are authenticated:

```powershell
$ProjectRoot = 'D:\Development\ThreeBodyLab'
New-Item -ItemType Directory -Force $ProjectRoot | Out-Null
# Clone only after the owner/name/visibility are agreed and the remote is created.
git clone https://github.com/BFH-coder01/3bodyproblem.git "$ProjectRoot\repo"
Set-Location "$ProjectRoot\repo"
```

Linux equivalent:

```bash
mkdir -p "$HOME/Development/ThreeBodyLab"
git clone https://github.com/BFH-coder01/3bodyproblem.git "$HOME/Development/ThreeBodyLab/repo"
cd "$HOME/Development/ThreeBodyLab/repo"
```

For an empty remote, seed the scaffold in a local `main`, commit it, and push the agreed baseline. For a populated remote, import through an ordinary bootstrap PR. Do not copy a `.git` directory from another machine. Authentication uses the machine's approved credential helper or repository app connection, not tokens in chat or committed files.

TBL-000 imports the existing Site code from its canonical source/export, preserving the source commit `945f1aeca3f3e11b516169ae9361bbeaaad11fdf` and inventorying `physics.js`, `scan.js`, `orbit.js`, `worker.js`, `replay-filter.js`, viewer files and existing tests. Initially place this under a clearly labelled baseline path. Capture current fixture outputs before refactoring. Do not copy Site credentials or deployment identity into the new repo.

## 2. Inventory before installing

Record `git --version`, Python version, OS build, GPU name/device ID, driver version, installed runtime/compiler versions, RAM and free local disk. On Windows, Task Manager/Device Manager or approved GPU tools can verify the device; on Linux use the installed AMD inspection tools if available. Record raw output privately as environment evidence. A label saying `gfx1100` without an actual device-backed run is not GPU validation.

Choose either native Windows HIP SDK or native Linux ROCm with an officially supported OS/driver/runtime tuple. The RX 7900 XTX appears in AMD's support documentation for both routes. Installed versions must be checked on the actual rig; do not upgrade or replace drivers automatically. WSL is a distinct optional environment with its own compatibility check.

Use a dedicated local evidence root. Windows examples: `D:\Development\ThreeBodyLab\data` and `...\artifacts`. Linux examples: `~/Development/ThreeBodyLab/data` and `.../artifacts`. If possible put bulk replay data on the less-contended SSD after measuring I/O. Keep all bulk data outside Git.

## 3. Create task workspaces

Each machine has one root clone plus sibling worktrees. Example tasks:

| Role | Local task worktree example | Scope |
| --- | --- | --- |
| Coordinator | `repo` plus detached integration worktrees | Dispatch, ledger and integration. |
| Numerical agent | `worktrees/tbl-020-numerical-a` | Reference core/CLI and its task tests. |
| Scheduler agent | `worktrees/tbl-030-scheduler-a` | Coordinator leases, database and API tests. |
| Viewer agent | `worktrees/tbl-040-viewer-a` | Viewer adapter and visual behavior tests. |
| GPU agent | `worktrees/tbl-070-gpu-a` | HIP backend and hardware fixtures. |
| Verifier | `worktrees/verify-<head-sha>` | Detached exact-head verification, no unrelated changes. |

Tasks in this pack start `planned`. The coordinator confirms dependencies and authorization, changes a dispatched task to `ready` in the agreed dispatch source, and records its accepted base. The helper checks that a task is ready and its role matches; dependency acceptance, exclusive assignment and remote authority remain coordinator responsibilities.

Dry run, from the repo root (use `python3` on Linux or the installed `python`/`py -3` on Windows):

```bash
python scripts/workspaces.py plan --repo . --task TBL-020 --agent numerical-a --role numerical --base origin/main
```

After the task is ready:

```bash
python scripts/workspaces.py create --repo . --task TBL-020 --agent numerical-a --role numerical --base origin/main --fetch
```

`--fetch` explicitly refreshes `origin` when creating. The helper resolves the base to an immutable commit, refuses a dirty root clone, an existing destination, or an existing branch, and uses argument arrays rather than shell interpolation. Its JSON output includes the worktree, named branch, base SHA and a local assignment-envelope path under the sibling worktree root. Pass that envelope to the agent; do not rely on an older task template inside the frozen worktree for current dispatch authority.

Do not manually switch a branch into two worktrees at once or use `--force` to evade Git's branch checks. If using a Codex-managed detached worktree instead, bind it to the assigned task branch before committing/pushing, or let the coordinator create a branch at its returned commit. Do not nest two worktree-management mechanisms around the same task.

## 4. Work independently and return evidence

The agent starts in its worktree, reads root/nested instructions, reads the assignment envelope, confirms the base SHA and permitted paths, implements only its task, and pushes its own branch once that capability is authorized. Open a draft PR with the handoff template. Another machine starts from its own clone and fetches the branch or accepted base through Git.

Use local build directories per worktree (`build/` or `out/`) and environment-specific dependency caches. Do not share writable build outputs between branches. A GPU agent submits a hardware test reservation; only one benchmark or parity run holds the GPU slot. Pause competing local LLM GPU workloads through the user's agreed procedure before controlled performance measurements.

The verifier uses the detached returned-head procedure in the Git model. The coordinator runs an integration candidate against current main and merges only after gates pass. On completion, remove a worktree only when clean and fully handed off; do not prune or delete another active agent's worktree.

## 5. Recovery

A failed agent leaves its branch, local changes and task envelope for inspection. The coordinator records the last pushed SHA and reassigns to a new worktree or resumes the existing one after verifying ownership. Never assume an agent's unpushed local commit exists on a different machine. Runtime leases recover numerical work separately; a development-agent handoff does not manipulate simulation leases.

Worktrees and agents do not provide unattended orchestration by themselves. For continuing work while this chat is idle, provision an explicitly authorized local runner/automation with durable task state, logging, budgets and a stop mechanism. No such persistent runner is installed by this pack.
