# Derived documents never invent identifiers

Notes and Topics are regenerated from scratch on every pipeline run, so any identifier the
pipeline chooses freely would drift between runs — producing link rot, an unstable graph
and unreadable diffs, and destroying the replayability that ADR-0002 exists to provide.
We therefore constrain every derived document to an identity it inherits rather than
invents: a **Note** is 1:1 with its Capture and takes that Capture's identity, and a
**Topic** is derived from every Note that mentions an entity and takes that entity's
canonical name.

## Considered Options

- **One Note per Capture only (1:1)** — simplest, but a ten-minute dictation covering three
  unrelated subjects stays a single blob, which makes the graph meaningless because every
  Note is about everything.
- **Pipeline splits a Capture into N atomic Notes** — gives a properly atomic knowledge
  base, but the pipeline must name each fragment. An LLM re-run may emit two Notes instead
  of three, or name them differently, so every regeneration churns the graph.

The Note/Topic split was chosen because it delivers atomicity at the Topic layer — where
the user actually reads by subject — without anything having to invent an ID.

## Consequences

Section 4 of the PRD collapses into the pipeline: the "auto-generated Wiki" and its entity
extraction are not a separate feature, a Wiki page *is* a Topic.

Regeneration now has two modes. Notes are a per-file map and are trivially parallel; Topics
form a dependency graph, since one new Capture invalidates every Topic it touches.

This invariant is only as strong as entity resolution. Topic identity is stable only if the
canonical name for an entity is stable — see ADR-0005.
