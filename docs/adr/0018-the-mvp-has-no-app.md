# The MVP has no app; Obsidian is the interface

Ranked by what could actually kill this project, the risk is concentrated almost entirely in
the pipeline: whether derived Notes and Topics are worth reading at all, whether Contribution
churn behaves as ADR-0010 models it, and whether the Candidate review loop is tolerable in
daily use. The client-side index and the Git write-back path are standard, low-risk work. A
first release that spends its effort on the PWA would therefore validate the safest part of
the system.

The MVP ships a pipeline and nothing else. Obsidian — already a markdown reader with search,
backlinks and a graph view — is the entire interface. Two decisions already made are what
make this possible: **ADR-0017 makes typing a first-class capture path**, so day-one capture
is typing a file into the vault with no hotkey, Whisper or mobile app; and **the review loops
are just files** — `candidates.md` is generated, `registry.md` is human-written, and promotion
is moving a line between them in Obsidian. That is the derived/decided split of ADR-0011
expressed as two files, and it needs no UI at all.

## Slices

1. One Capture in Git → Cloud Run Job → Note committed back. The tracer bullet: touches every
   architectural layer once and yields a readable Note.
2. Contributions → Topics, gated by a hand-written Registry. Tests the map-reduce model, churn
   behaviour, and whether Topic pages are worth reading.
3. `candidates.md` / `items.md` review loops. Tests whether promotion friction is tolerable.
4. Desktop hotkey and local Whisper, Registry-biased.
5. Mobile share-target capture.
6. PWA and client-side index — only once Obsidian demonstrably stops sufficing.

## Consequences

**Slices 1–3 are a decision point, not a milestone.** They reveal whether derived Topics are
useful. If they are not, the response is to fix enrichment rather than proceed to slice 4, and
having built no app is what keeps that cheap.

**The PWA may never be built.** That is the plan working rather than failing: if a good
pipeline plus Obsidian is sufficient, the PWA was never the product, and learning that costs
nothing here.
