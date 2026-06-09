# KNOWN_MISMATCH — prose describes one feature, gold+test grade another

A defect class distinct from everything else in this audit. It is **not** underdetermination (a
two-expert split, where two faithful readings diverge) and **not** KNOWN_BAD (gold fails its own
grader). Here the gold **passes** its grader and the test is internally valid — but the task **prose
describes a different feature than the one the gold implements and the hidden test checks**. No reading
of the prose, however careful, produces the graded behavior. A solver is asked to build feature X and
graded on feature Y.

Surfaced incidentally by the two-expert advocate pass (a model charged to find missed ambiguity flagged
it as a different kind of break). A systematic mismatch scan over the full public set is a separate pass,
not yet run — so this is "≥1 confirmed," not a rate.

## flipt-io_358e13bf  — snapshot-cache deletion vs CSRF/config

`instance_flipt-io__flipt-...` (repo `flipt-io/flipt`)

**The prose asks for snapshot-cache reference deletion** (`data/cases/flipt-io_358e13bf/spec.md`):

> Title: *Snapshot cache does not allow controlled deletion of references* … The snapshot cache lacked a
> way to remove references explicitly … Fixed references cannot be deleted and remain accessible.
> Non-fixed references can be deleted and are no longer accessible after removal.

**The gold patch and hidden test grade a CSRF/config feature** — a different subsystem entirely:

- `gold.diff` touches `internal/config/authentication.go`, `internal/cmd/http.go`,
  `config/flipt.schema.{json,cue}` — configuration/auth, not the snapshot cache.
- `hidden_test.diff` is `internal/config/config_test.go`, asserting a `csrf.secure` config default —
  nothing about reference deletion.

The two are disjoint: an engineer who implements the described `SnapshotCache.Delete` (fixed vs
non-fixed reference removal) makes no change to `config_test.go` and fails the grade. The grade measures
a feature the prose never mentions.

**Receipt (grep-checkable, no model judgment):** the prose title/body name only the snapshot cache; the
gold's changed files and the test file are all under `internal/config` / `internal/cmd`. Verify by
reading `spec.md` against `gold.diff` + `hidden_test.diff` at the pinned commit.

## Related but distinct — test exercises prose-unmentioned internals

`qutebrowser_ef62208c`: the prose says *"No new interfaces are introduced,"* yet the hidden test imports
and exercises several new private helpers (`copy_add_setting`, `prefixed_settings`, `switch_names`,
`chromium_tuple`). This is a fairness gap (the test depends on internals the spec disclaims), but it
fails *both* faithful implementations equally, so it is not a two-expert split and not a feature
mismatch — it is "test references unspecified internals." Logged here for adjacency; it is not counted
in the mismatch tally.
