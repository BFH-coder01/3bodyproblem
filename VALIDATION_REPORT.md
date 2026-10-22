# Foundation validation report

Executed 23 October 2026 in the hosted Linux workspace. Author-run evidence; independent review and hosted CI results remain separate acceptance requirements.

- Repository base: `b28db6ab55106c5a4a998fc441f4199f3b78ed8a` (initial README and MIT LICENSE).
- Previous branch head: `420def48cecb27dde9d529ab3fdd8133620bba76` (planning/tooling foundation).
- Browser source: `945f1aeca3f3e11b516169ae9361bbeaaad11fdf`.
- Environment: Python 3.12.14; Node v24.19.0; Git 2.51.1; Linux.
- `python3 -m unittest discover -s tests -v`: all 8 tests passed using temporary real Git repositories.
- `node baseline/tests/physics-scan.cjs`: all assertions passed, covering exhaustive small-grid enumeration, direct resume, all-rest gravity on all bodies, close encounters, escapes, recurrence reference, insufficient cycles and replay filters. Reference period: 5.713338304503539; all-rest short escape: 4.769 simulated seconds.
- `sh -n scripts/new-agent-workspace.sh`: passed.
- `python3 scripts/validate_bootstrap.py`: validates the inventory hashes, 15 task manifests, dependencies and experiment JSON.
- Byte comparison against the pinned Site checkout: all eight runtime files and the test match exactly.

Raw author-run output is in ops/evidence/TBL-000-import.json. PACK_MANIFEST.json hashes the tracked source and documentation inventory (excluding itself).

The owner requested commit and push after being informed that importing the private Site source would publish it to this public repository. This update includes the approved source and tests; it excludes Site deployment identity, credentials, Git internals and the unused precomputed dataset described in baseline/README.md.

The Windows wrapper, Windows filesystem behavior, RX 7900 XTX, HIP toolchain, branch protections, native solver and multi-machine runtime remain untested. The CPU CI workflow now includes browser physics/replay tests; hosted CI for a new head must be checked separately. No rig workspace, driver installation, remote agent, model change or main-branch merge is included. TBL-000 remains in review pending independent verification and acceptance.
