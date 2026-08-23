# Items are proposals; accepting one promotes it to a Task

Items — tasks, questions and decisions the pipeline extracts — live inside Notes, which are
pipeline-owned and read-only. So under the rules as written the user cannot check off a
todo, because doing so is decided state on a derived artifact (ADR-0011).

Storing completion in a side file keyed by the Item's text does not fix it. An Item is text
an LLM extracted, so its key is an invented identifier (ADR-0004): stable while Contributions
stay cached, but orphaned by any full corpus replay — which ADR-0010 makes a routine
operation the user will run often while iterating on prompts.

An Item is therefore a **proposal**. Accepting one creates a **Task**: a decided artifact
with its own stable identity that references the Note it came from. This reuses the
Candidate-to-Registry pattern rather than introducing a third mechanism — the pipeline
proposes, the user promotes, and the promoted thing is human-owned and durable.

## Considered Options

- **Items are read-only; todos go to a separate task app** — keeps the model pure and adds no
  machinery, but discards something the Captures already contain.
- **A human-owned state file keyed by `hash(note_id + item text)`** — lowest friction, but its
  keys are derived from LLM-authored text and do not survive a replay.

## Consequences

Promotion doubles as triage, which is wanted anyway: not every "I should look into that" said
into a phone deserves to become a task. It happens on the same review surface as Candidates
and unresolved Sources.

A Task outlives the Item that produced it. If a replay re-derives the Note and the Item is
worded differently or absent, the Task is unaffected — it is decided state, and decided state
is never regenerated.
