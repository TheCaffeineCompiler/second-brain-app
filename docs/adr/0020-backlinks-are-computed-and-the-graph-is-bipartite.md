# Backlinks are computed, and the graph is bipartite

§3 asks the pipeline to inject links to related past notes at the bottom of each document.
Taken literally that is incompatible with ADR-0010: injecting Note Z as a backlink into Notes
A, F and Q means every new Capture rewrites old Notes, so churn grows with corpus size rather
than with the day's activity — the exact property ADR-0010 exists to guarantee.

**Backlinks are therefore never stored.** They are a view computed from forward links, by
Obsidian's backlink pane today and by the client index later. Storing both directions of an
edge duplicates the data and makes the duplicate churn.

**There are no Note-to-Note links.** A Note links to the Topics it makes claims about and to
its Source, and to nothing else. Two Notes discussing LLMs are already connected through
`topics/llm.md`, and that connection is better than a raw backlink because it is *labelled* —
the reader knows why the two are related. An unlabelled "related notes" list is plausible
adjacency that tells the reader nothing. The resulting graph is bipartite, with Topics as hubs
and Notes as leaves, so every edge is explainable — as against a Note-to-Note similarity
graph, where everything is faintly similar to everything and §6's graph view becomes
ornamental.

**A link exists if and only if a Contribution exists.** A Note that mentions a Topic in passing
without making a claim about it earns no edge. Link generation is therefore not a pipeline
stage at all; it is already the output of ADR-0010's map step.

## Semantic similarity proposes Candidates

§3's underlying intent — surfacing hidden connections — survives, but its output is a proposal
rather than an edge. Where two Notes are genuinely related and no Topic connects them, that is
a signal a **Topic is missing**. Clustering over Contributions surfaces it as a Candidate, the
user names it, and the link then appears through the Registry, explainable. This is ADR-0005's
refusal to guess applied one level up.

## Consequences

A connection cannot exist until the Topic carrying it has been named, so there is latency
between noticing something recurring and it becoming navigable. This is accepted deliberately:
an unnamed connection is not yet knowledge.

This decision removes a pipeline stage rather than adding one.
