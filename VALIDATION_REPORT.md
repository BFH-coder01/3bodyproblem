# Foundation validation report

Author-run evidence in the hosted Linux workspace; independent review and hosted CI results remain separate acceptance requirements.

- Repository base: `b28db6ab55106c5a4a998fc441f4199f3b78ed8a` (initial README and MIT LICENSE).
- Environment: Python 3.12.14; Git 2.51.1; Linux.
- `python3 -m unittest discover -s tests -v`: all 8 tests passed using temporary real Git repositories.
- `sh -n scripts/new-agent-workspace.sh`: passed.
- `python3 scripts/validate_bootstrap.py`: checks the SHA-256 inventory, all 15 task manifests, dependency resolution/cycles and experiment JSON.

This branch contains the requested planning material and newly authored workspace tooling. It excludes the private Site browser source, deployment identity and credentials. Automatic approval review requires explicit owner approval before that source can be published to the public repository. TBL-000 therefore remains incomplete and in review.

The Windows wrapper, Windows filesystem behavior, RX 7900 XTX, HIP toolchain, branch protections, native numerical solver and multi-machine runtime remain untested. This branch adds a real workspace/inventory CPU CI workflow; local results are not a claim that GitHub Actions has passed. No rig workspace, driver installation, remote agent or main-branch merge is part of this foundation.
