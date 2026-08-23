# The user is the sole naming authority for Topics

ADR-0004 makes Topic identity the entity's canonical name, which only holds if that name is
stable across pipeline runs. An LLM choosing it is not stable — one run resolves a mention
to `acme`, the next to `acme-corp`, leaving two half-empty pages, a split graph and broken
inbound links. Naming authority therefore sits with the user: a human-written **Registry**
lists canonical entities and their aliases, and the pipeline may only resolve a mention to
an entity already registered.

To avoid a cold start where an empty Registry means nothing ever resolves, an unregistered
mention becomes a **Candidate** rather than a Topic. Candidates are surfaced as a review
list the user works through, promoting, renaming or merging them into the Registry. There
is no automatic promotion on a recurrence threshold — recurrence counts only order the
list. A Topic exists only once the user has registered it.

## Considered Options

- **Registry-only, no Candidates** — fully deterministic, but nothing resolves until the
  user has hand-written the Registry from nothing.
- **Agent free-creates Topics, merge tooling cleans up afterwards** — no curation burden,
  but reintroduces unstable identity and the exact tag sprawl and hallucination the PRD
  sets out to prevent. Merges become migrations.

## Consequences

**The Registry is a human-written artifact**, subject to the single-writer rule like a
Capture. The pipeline writes Candidates; it must never write the Registry, or naming
authority becomes circular and the guarantee is lost.

**Contextual references are left unresolved.** The Registry resolves lexical variants
("Acme Corp", "ACME"). It cannot resolve "those guys from the Tuesday call", and the
pipeline must not guess — a wrong resolution silently attributes content to the wrong
Topic and goes unnoticed, whereas an unresolved mention is visible and harmless.

**Renaming a Topic is a supported operation**, not an accident: edit the Registry, delete
the Topic, replay. This stays cheap only as long as nothing but the Registry refers to a
Topic by path.
