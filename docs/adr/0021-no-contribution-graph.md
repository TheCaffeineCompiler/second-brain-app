# No contribution graph; dormancy is the useful signal

§6 asks for GitHub-style contribution graphs and burndown charts covering both "note-taking
consistency" and "focus areas over time". These are two features in one bullet, and the first
is rejected outright rather than deferred.

**A streak counter is a liability in this system specifically.** A contribution heatmap rewards
volume of Captures, but the system's value is quality of thought, and the two are in tension:
once a streak is on screen, the user captures something to keep it alive. The Registry then
fills with Candidates drawn from throwaway Captures and Topic syntheses are diluted by filler
Contributions — degrading exactly the enrichment quality that ADR-0018 identifies as the whole
bet, silently and without any test failing. A metric that can corrupt the corpus it measures
is not worth building.

**Dormancy is the signal worth surfacing.** What the user has done is already visible in the
Vault; what is useful is what has stopped and what is quietly accumulating — Topics with no
Contribution in ninety days, Candidates never reviewed, Sources still `unresolved`, Tasks open
and ageing. That is not a vanity chart but **the state of the review loops**, which is what
keeps ADR-0005's naming authority from decaying: if the Candidate list is abandoned, ADR-0005
collapses, and this view is what would show it.

## Consequences

The dormancy dashboard is deferred to slice 6. It is a pure view over derived data — no
artifact, no storage, no pipeline stage — and needs no data model change, because a
Contribution derives from a Note whose Capture identity is already a timestamp. In an MVP
where Obsidian is the interface it has nowhere to live in any case.

**Slice 3 therefore needs attention rather than instrumentation.** The dashboard is what would
otherwise reveal that promotion friction has become intolerable; without it, that has to be
noticed by hand.
