# Native FP64 reference: isolated additive contract

This increment ports the accepted JavaScript integrator to pure C++17 functions for cloud validation. It does not change the pipeline-v1 protocol, accepted physical model, production worker selection or database schema. Native results remain validation-only until parity/uncertainty evidence supports a later reviewed adapter. No rig, HIP or stable-orbit proof is implied.

Accepted upstream: d5cf5342bad7c09d1dd3531de2af6076808e7a5d. Coordinator owns this contract, frozen native/include/threebody.hpp, build tooling, CI and integration. Separate core, CLI and parity-test agents own disjoint worktrees. Independent verification follows integration. Current authority from ops/ACTIVE_PROCESS.md continues; no driver, deployment, model or protocol-breaking change.

## C++ interface

Frozen header is authoritative. `grid`, `triple_at`, `initial`, `acceleration`, `energy`, `fixture` and `simulate` have no shared mutable state and do not mutate caller inputs. Constants and baseline event/timestep ordering remain exact: adaptive kick-drift-kick, 0.015 m close stop, square ±6 m, μ=9.80665, 1% energy error, 2,000,000-step baseline guard. Preserve sampling/decimation and final-frame behavior. All search states start at rest; comparison fixtures are explicitly separate.

Validate finite inputs and representable FP64 arithmetic; radius [0.1,2], 0<duration<=300, 0<dt<=0.002. Public triple_at bounds N to [3,14161] (maximum supported grid), preventing uint64 combinatorial overflow. Reject out-of-range ordinals before mutation. Singular initial states may be classified Close encounter with natural nonfinite energy represented as null at the JSON boundary; do not soften them. Arithmetic overflow must not return nonfinite physical-state vectors. Invalid input throws std::invalid_argument/out_of_range, and CLI maps it to a nonzero error response. Emit IEEE double values with max_digits10. No fast math; disable floating-point contraction where supported.

Comparison fixtures: `asymmetric-rest` p[-3,-2,1,-1,2,3], v0; `collinear-rest` p[-2,0,0,0,2,0], v0; `figure-eight` and `lagrange-triangle` reproduce baseline preset('eight'/'triangle'); `fast-escape` p[-2,0,0,0,2,0], v[-20,0,0,0,20,0]. Nonzero-velocity fixtures are tests only, never scan initial conditions.

## CLI

`native/cli/main.cpp` supports one structured argv operation per invocation:

- `native-reference --radius 2 --ordinal 57 --duration 6 --dt 0.002` simulates a rest-start scan trial; defaults radius0.25 ordinal0 duration30 dt0.002.
- `--fixture NAME --duration N --dt N` runs an explicitly labelled comparison fixture, incompatible with explicitly supplied radius/ordinal.
- `--describe --radius R` returns `{protocol:"threebody.native-reference.v1",engine:"native-fp64-v1",grid:{radius,n,N,total:"decimal"},build:{compiler,precision:"fp64",fast_math:false}}`.
- `--initial --radius R --ordinal I` returns same protocol/engine/build plus `{initial:{p,v},triple:[a,b,c]}` without integrating.
- `--acceleration` followed by exactly six finite position arguments returns `{acceleration:[6]|null}` plus protocol/engine/build. No other simulation flags allowed with this operation.

Simulation output: `{protocol,engine,build,input:{radius,ordinal:"decimal"}|{fixture},result:{engineVersion:2,initial:{p,v},frames:[[t,...p]],velocityFrames:[[v]],outcome,time,energyError,minSeparation,steps,initialEnergy,finalEnergy,finalVelocity:[6],options:{duration,dt,mu:9.80665,boundary:6,close:0.015}}}`. Nonfinite diagnostic values serialize as null, never invalid JSON. Orbit screening is left to the existing JavaScript analyzer on this raw record. All successful operations print exactly one JSON object and exit0. Invalid/unknown/duplicate/missing flags and malformed/noncanonical/overflow ordinals print `{error:{code:"invalid_input",message:...}}` on stderr and exit2, without success stdout. No shell execution/dependencies. Numeric flags accept strict decimal/scientific syntax; reject nan/inf/hex/trailing junk.

## Build and parity harness

Coordinator provides scripts/build_native.py with `build(output,cxx="c++") -> metadata`; sources native/core/threebody.cpp and native/cli/main.cpp, include native/include. CLI `python3 scripts/build_native.py --out build/native-reference` emits JSON metadata including compiler command/version, flags, source digests and binary digest; no downloads. Python3.11+ and a C++17 compiler required. CI builds/runs native tests on hosted Linux; Windows remains explicitly untested unless actually executed.

Parity tests independently compile and call the real binary and Node baseline. Baseline remains byte-for-byte unchanged. Require exact enumeration/initial-state agreement on all small supported N and sampled grid extremes, finite/asymmetric forces and net cancellation, analytic inverse-square checks, short-trajectory parity, rest-start close/escape fixtures, nonzero comparison fixtures, frame endpoints, repeat calls and option rejection. Do not require every long chaotic trajectory to match exactly; report event/timing/diagnostic discrepancies explicitly and keep any failed case out of accepted native parity. Fixed short-run tolerance: abs+relative 1e-9 for positions/velocities/energies at <=0.1s; outcome must agree for designated fixtures; their time tolerance max(1e-8,4dt). No weakening after seeing results without a documented finding.

Broader cloud comparison samples ordinals from distant ranges and reports classifications, event timing, source/build identity and disagreements. An accepted report requires the builder sidecar to match the executable hash, current native source hashes, strict FP64 flags and recomputed build identity; missing or stale provenance is an error. This linkage is not attestation against a malicious publisher. No native backend is enrolled into the production ledger by this increment. Do not extrapolate CPU timings to GPU throughput.
