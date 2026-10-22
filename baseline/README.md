# Browser baseline

Imported without code edits from Three-Body Orbit Lab at source commit `945f1aeca3f3e11b516169ae9361bbeaaad11fdf`. The eight runtime files under dist/ and the test under tests/ are byte-for-byte copies. Root PACK_MANIFEST.json records their SHA-256 hashes. The owner authorized committing and pushing this source after being informed that this repository is public.

## Run

```bash
python3 -m http.server 8000 --directory baseline/dist
```

Run from the repository root and open http://localhost:8000. An HTTP server is required for the Web Worker.

## Behavior

All enumerated search trials start with three equal masses at rest. Each body receives mutual inverse-square gravity. Every escaped outcome is shown regardless of duration; other outcomes require more than five simulated seconds. Close encounters stop the point-mass model; there is no mass merging. Finite recurrence is an orbit candidate, not proof of permanent stability. This implementation uses a serial CPU worker; the native distributed solver and HIP kernels remain roadmap work.

The figure-eight and deliberately launched escape fixtures in the tests use nonzero initial velocities only as numerical reference cases. They are not the enumerated search experiment.

## Import inventory

Included: app.js, index.html, orbit.js, physics.js, replay-filter.js, scan.js, style.css, worker.js, and tests/physics-scan.cjs. Excluded: unused precomputed dist/baseline.json (no runtime references; predates the current all-rest radius scan), Site hosting metadata, deployment identity, credentials and Git internals. The original Site deployment is unchanged.
