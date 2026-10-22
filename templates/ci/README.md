# CI implementation specification

No fake passing workflow is included. TBL-000 establishes actual bootstrap checks, then later tasks add real named checks as components become runnable.

Hosted CPU runners: contract/schema tests, fixtures, enumeration/coverage, lease/restart tests, Linux/Windows host builds, and module-specific tests. Use minimal read permissions by default; PR workflows do not need repository write permission merely to compile/test. Pin dependency versions and action revisions according to the repo policy.

Trusted rig runner: manual/coordinator-approved dispatch to a pinned commit for `hip-smoke`, `hip-parity` and controlled benchmarks. Labels identify the actual OS and RX 7900 XTX environment. Serialize all jobs using a single GPU concurrency group plus a local exclusive device lock. Avoid a cancellation policy that silently kills an evidence-producing run.

Do not execute arbitrary fork PR code on a long-lived machine containing user credentials or private files. Use approved code and a dedicated limited account/isolated runner. GPU access itself must be explicitly configured; a container label is not proof of isolation or a real GPU run. Record environment inventory and raw command logs as artifacts, excluding credentials.

Protection gates must name real checks and, where supported, the expected provider. GPU jobs that did not run are not success. Routine non-GPU documentation changes should not require an unavailable GPU job; encode and review applicability explicitly rather than marking an unexecuted scientific test as passed.
