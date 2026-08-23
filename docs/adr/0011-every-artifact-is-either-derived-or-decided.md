# Every artifact is either derived or decided

Working through where a checked-off todo could live exposed the principle the earlier
decisions had been circling without naming. Every artifact in the system belongs to exactly
one of two classes:

- **Derived** — pipeline-owned, disposable, rebuilt from scratch at will. Notes, Topics,
  Contributions, Sources, Candidates.
- **Decided** — human-owned, durable, never regenerated. Captures, the Registry, Tasks.

Nothing is both, and the combination the model deliberately has no room for is *decided
state living inside a derived artifact*. That is precisely what a completed todo would be
if Items carried their own done-state, and precisely why it needed a different answer
(ADR-0012).

Almost every rule already agreed is a consequence of this split: single-writer ownership
(ADR-0002), read-only derived artifacts (ADR-0003), identity that is inherited rather than
invented (ADR-0004), and replay-instead-of-migrate (ADR-0010).

## Consequences

The test for any new feature is which class its state belongs to. If it is decided state,
it needs a durable human-owned home with stable identity of its own — never a field on a
derived artifact, which a replay would destroy.

Derived artifacts may be deleted at any time without loss. Decided artifacts may never be
regenerated, so they must be backed by Git history and treated as precious.
