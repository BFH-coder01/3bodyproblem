# Running the stateless CPU pipeline

This increment implements the existing point-close-stop model with a headless JavaScript reference worker, a durable Python coordinator and an independent replay viewer. Node 18+ and Python 3.11+ are required. No third-party Python packages are needed. All paths below are relative to the repository root. The ledger stores data outside version control.

## Local campaign

```bash
python3 -m services.pipeline init --db data/demo.sqlite --radius 2 --duration 6 --start 0 --count 60 --chunk-size 5
python3 -m services.pipeline run --db data/demo.sqlite --workers 2
python3 -m services.pipeline status --db data/demo.sqlite
python3 -m services.pipeline serve --db data/demo.sqlite --host 127.0.0.1 --port 8765
```

On Windows use `python` in place of `python3` if appropriate. Open http://127.0.0.1:8765. The 60-trial demo includes short encounters, a longer interaction and a real rest-start escape before five seconds. The table contains all accepted trials. Automatic playback includes every escape and other trials lasting strictly more than five simulated seconds.

Changing playback speed affects only the viewer. Compute never waits for an animation. The requested ordinal range is a bounded campaign, not an exhaustive stability search. `Bounded` means the recorded run stayed inside the observation square; an orbit candidate remains numerical evidence rather than a permanent-stability proof.

## Multiple machines

Every worker machine has its own clone at the same accepted source commit, Node and Python. Run the coordinator once on a trusted research LAN, explicitly choosing its LAN interface:

```bash
python3 -m services.pipeline serve --db data/campaign.sqlite --host YOUR_LAN_IP --port 8765
```

On each worker, from its clone:

```bash
python3 -m workers.cpu_worker --url http://COORDINATOR_LAN_IP:8765 --worker-id rig-a
```

Use a different worker ID for each concurrent worker. The coordinator alone writes SQLite; do not place a shared SQLite database or Git worktree on a network filesystem. Workers request structured leases and invoke the checked-in reference CLI. They never execute commands supplied by the server. This first API has no authentication or TLS termination: keep it on a trusted LAN and do not expose the port to the internet. Add a separately reviewed authenticated transport before broader distribution.

A worker exits when no lease is available. Restart it to join later work. A dropped lease becomes available after its deadline; a late worker's old epoch cannot publish results. Accepted retries are idempotent, with unique trial coverage. Stop assigning new work by stopping workers/coordinator; restarting the same database preserves accepted results and expires abandoned leases. Local `run` failures return a nonzero status rather than silently retrying forever.

## Function boundaries

`describe(manifest)` normalizes the experiment and hashes its identity. `simulate(manifest,ordinal,replay)` creates fresh physical state and returns a complete result. `execute_lease` supervises only these known functions. The ledger owns leases, retries, publication and coverage; the viewer owns presentation. Protocol and payload details are in `contracts/pipeline-v1.md`.

Use `python3 -m unittest discover -s tests -v`, `node tests/reference-pipeline.cjs`, and `node baseline/tests/physics-scan.cjs` for acceptance. GPU acceleration and native FP64 parity remain subsequent gates. No RX 7900 XTX execution is implied by a CPU worker running on that machine.
