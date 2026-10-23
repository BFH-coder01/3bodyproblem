# CPU reference pipeline contract v1

Coordinator-owned interface, frozen for this increment. This wraps the accepted browser point-close-stop behavior without changing scientific policy. Native/HIP implementations follow parity and actual hardware gates. Functions receive all physical input in a manifest; persistent orchestration lives in the ledger.

## Reference functions and NDJSON

`workers/reference-cli.cjs` exports `describe(manifest)` and `simulate(manifest, ordinal, replay=true)` and is also an NDJSON stdin/stdout CLI. One output per input: `{ok:true,result:...}` or `{ok:false,error:{code,message}}`; malformed lines must not corrupt later valid lines. No logging to stdout other than protocol lines. Maximum input line 64 KiB.

Manifest canonical order/keys: `{protocol:"threebody.pipeline.v1",model:"point-close-stop-v1",radius:2,duration:6,dt:0.002}`. Unknown keys and unsupported versions/models are errors; missing radius/duration/dt default to 0.25/30/0.002. Each is a finite number; radius uses baseline range [0.1,2], 0<duration<=300, 0<dt<=0.002. Canonical JSON is JSON.stringify of that normalized ordered object. `experiment_id` is SHA-256 hex of canonical UTF-8 JSON. Ordinals on the wire are canonical unsigned decimal strings; require safe-integer conversion for this baseline's actual grid. No numeric coercion or leading zeros.

Input `{op:"describe",manifest:{...}}` returns `{manifest,experiment_id,total:"1794096784"}` for defaults. Input `{op:"simulate",manifest:{...},ordinal:"0",replay:true}` returns the result below. Replay defaults true and must be boolean if supplied.

Simulation result: `{protocol,experiment_id,trial_id,ordinal,engine:"js-baseline-v2",precision:"fp64",outcome,time,initial:{p:[6],v:[6]},final:{p:[6],v:[6]},steps,energyError,minSeparation,orbit,replayEligible,replay}`. `trial_id=experiment_id+":"+ordinal`. Outcome and numeric behavior match the unmodified baseline. All search velocities are zero. `orbit` is the baseline analyzer result (candidate evidence only). Nonfinite minimum separation becomes null; all transmitted numbers must be finite. `replayEligible` uses the existing replay filter. `replay` is null unless requested AND eligible; otherwise `{frames:[[time,...6positions],...],velocityFrames:[[6velocities],...]}`. Final position comes from the final frame. No engine state is shared across calls. Reference functions must not mutate the caller manifest.

Descriptors, leases and results also carry `solver_digest`: SHA-256 of the reference adapter and physics/scan/orbit/replay-filter baseline source, using repository-relative path + NUL + normalized UTF-8 byte count + NUL + UTF-8 content for each path in that order. CRLF is normalized to LF. The reference adapter records its exact file list. An experiment pins this digest when created; re-init never changes it. Workers with a different source build cannot publish into that campaign. Results record `runtime:{node,platform,arch}` as execution evidence. This is source provenance, not proof that an untrusted remote worker executed faithfully.

## Durable orchestration

Python 3.11+ standard library. `services/ledger.py` owns transactional SQLite state; only the coordinator process writes the ledger. Clock injected for expiry tests. Decimal-string ranges are half-open, bounded by describe.total. Init validates via the Node describe operation before inserting immutable manifest and tasks. Default lease 60 s; expiry requeues a task with incremented epoch. Heartbeat requires current epoch/worker and unexpired lease. Publication is atomic for a complete task range; reject gaps, duplicates, wrong trial/experiment IDs, wrong epoch/worker, out-of-range or malformed results. Reject nonfinite values, malformed vectors/replay, impossible classifications and invalid durations before committing. Identical accepted retries are idempotent; conflicting retries rejected. Coverage counts unique accepted trials, including numerical/unresolved outcomes. Transactions and process restarts preserve coverage.

`services/pipeline.py` CLI: `python3 -m services.pipeline init --db PATH --radius 2 --duration 6 --start 0 --count 60 --chunk-size 5`; `run --db PATH --workers 2`; `status --db PATH`; `serve --db PATH --host 127.0.0.1 --port 8765`. Init prints experiment metadata. Run executes pending leases with bounded concurrent processes via `workers.cpu_worker.execute_lease(lease,node="node")`; that function returns a list of complete simulation results or raises. The main coordinator accepts all writes. Do not make each worker an independent ledger writer. Process/worker errors leave work retryable and visible; do not loop forever on a deterministic failure.

Lease object: `{task_id,experiment_id,manifest,start:"0",end:"5",epoch:1,worker_id,expires_at}`. `task_id` is an opaque string. Task chunks contain 1..32 trials; local worker counts are 1..64. API uses JSON, 16 MiB maximum request body, rejects invalid JSON/nonfinite values and returns `{error:{code,message}}` with an appropriate 4xx status. Local trusted research network only; no internet binding by default.

HTTP endpoints:

- `GET /v1/experiments` -> `{experiments:[{experiment_id,manifest,start,end,total,accepted,pending,running,...}]}`. Counts represent the requested campaign range, not all grid permutations.
- `GET /v1/trials?experiment_id=ID&after=0&limit=50` -> `{trials:[summary without replay],next_after:"ordinal"|null}`. after is an exclusive ordinal cursor; omit it for first page. Return ordinal order; limit 1..200.
- `GET /v1/trials/ID/replay` -> summary plus `replay` or 404 when unavailable.
- `POST /v1/lease` with `{worker_id}` -> `{lease:object|null}`.
- `POST /v1/heartbeat` with `{task_id,worker_id,epoch}` -> `{ok:true}`.
- `POST /v1/results` with `{task_id,worker_id,epoch,results:[...]}` -> `{accepted:integer,idempotent:boolean}`.
- `GET /` serves viewer/index.html; `/viewer/...` serves only files under viewer/. No arbitrary file paths. Same-origin API; no permissive CORS.

`workers/cpu_worker.py` provides `describe_manifest(manifest,node="node")`, `execute_lease(lease,node="node")` using fixed reference CLI and structured stdin, never shell=True. Its remote CLI: `python3 -m workers.cpu_worker --url http://HOST:8765 --worker-id NAME`; heartbeat in flight; worker only receives known structured simulation parameters. Solver failure is visible and does not submit partial results. No arbitrary executable from API.

Viewer calls only these GET endpoints and never runs physics. It paginates the table of test number (ordinal+1), initial positions, outcome/time and final frame; selecting a retained replay animates red/green/blue points and trails. Automatic playlist selects all escapes and other time>5 outcomes; no stable-proof labels. Playback speed never changes physical time. Empty, loading, missing replay and failure states must be usable.

## Acceptance

Baseline tests remain unchanged. New Node tests check stateless parity and protocol faults. Python ledger tests exercise expiry, fencing, duplicate/conflict/gap rejection and restart. End-to-end CLI and actual HTTP worker tests reconcile unique coverage and retained replay. Viewer model tests cover playback and late distributed arrivals. Actual browser rendering is a separate UI acceptance item: the hosted browser cannot reach the local coordinator and the local Chromium download failed, so this remains pending rather than being claimed as passed. Independent verifier reports the exact integrated head and findings before coordinator merge.
