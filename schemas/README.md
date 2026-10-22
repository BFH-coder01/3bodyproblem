# Contract gate

TBL-010 must provide and validate actual manifest/task/result/replay schemas and canonicalization rules before runtime implementations depend on them. This directory intentionally contains no permissive schema pretending to be an accepted protocol.

The experiment JSON is a proposed example. Acceptance must specify enum migration, identifier hashing, decimal-string uint64 ranges, units, float encoding/invalid-value rules, payload bounds, lease epochs, diagnostics, evidence lineage and backward compatibility. Only the contracts owner changes shared schemas during concurrent task work.
