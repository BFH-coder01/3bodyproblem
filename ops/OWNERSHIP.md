# Proposed module ownership

| Paths | Implementation owner | Additional review |
| --- | --- | --- |
| contracts/, schemas/, docs/adr/ | Contracts owner / coordinator | Numerical lead for scientific semantics |
| native/core/, native/cli/ | Numerical agent | Independent numerical verifier |
| native/hip/ | GPU agent | Numerical verifier and platform owner |
| services/coordinator/ | Scheduler agent | Worker/integration verifier |
| workers/ | Worker agent | Scheduler owner |
| viewer/ | Viewer agent | Protocol owner for adapter changes |
| verification/, tests/fixtures/ | Independent numerical/test owner | Coordinator; fixture-author independence |
| root build files, dependency locks, .github/ | Coordinator or explicitly assigned owner | Relevant module owners |
| ops/, AGENTS.md, release config | Coordinator | Werner for authority/protection/release changes |

A task envelope narrows these scopes. This table is workflow ownership, not an OS or GitHub credential boundary. Replace role labels with real GitHub identities in CODEOWNERS only after identities/access are confirmed. Do not commit invalid placeholder handles to an active CODEOWNERS gate.
