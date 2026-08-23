# Second Brain

A personal knowledge system where the user dictates unstructured thoughts and an agentic
pipeline turns them into a structured, linked, searchable knowledge base. Everything is
markdown in a Git repository.

## Language

**Vault**:
The Git repository holding every Capture and Note.
_Avoid_: database, store, corpus

**Capture**:
A raw thought as the user recorded it, unedited by the system.
_Avoid_: raw note, brain dump, dictation, entry

**Note**:
A document derived from one or more Captures by the pipeline.
_Avoid_: enriched note, extended note, processed note

**Topic**:
A synthesis of what the user knows about a single entity — a person, organisation, concept
or source — plus an index of the Notes that mention it.
_Avoid_: wiki page, entity page, tag page, MOC

**Source**:
Where a Capture's material came from — a podcast episode, blogpost, book or meeting.
Identified by the world (a URL) rather than by the Registry.
_Avoid_: reference, citation, origin

**Task**:
An Item the user has accepted, becoming durable work the system tracks in its own right.
_Avoid_: todo, action, ticket

**Registry**:
The user-maintained list of canonical entities and their aliases; the only authority on
what a Topic is called.
_Avoid_: reference folder, taxonomy, vocabulary, index

**Candidate**:
An entity the pipeline has noticed in the Captures but which the user has not yet admitted
to the Registry.
_Avoid_: proposed tag, suggestion, unresolved entity

**Tag**:
A facet of a note itself — its kind or status — drawn from a small closed set. Unlike a
Topic, it has no page.
_Avoid_: label, category, keyword

**Kind**:
What sort of Capture a Note came from — one of `podcast`, `article`, `meeting`, `thought`.
Determined independently of the Source; disagreement between them is what flags missing
provenance.
_Avoid_: type, category, note type

**Item**:
A discrete actionable or open thread the pipeline extracts out of a Capture — a task, a
question, a decision — carried as structure inside the Note rather than as a Tag on it.
_Avoid_: todo, task, action item

**Contribution**:
The few structured claims a single Note makes about one Topic; the cached unit from which
Topic pages are assembled.
_Avoid_: extract, fact, snippet, chunk

**Enrichment**:
The act of deriving a Note from a Capture — tagging, linking, source resolution, cleanup.
_Avoid_: processing, ingestion

## Relationships

- Every artifact is either *derived* (pipeline-owned, disposable) or *decided* (human-owned,
  durable); **Captures**, the **Registry** and **Tasks** are decided, everything else derived

- The **Vault** contains **Captures**, **Notes**, **Topics** and the **Registry**, in separate regions
- **Enrichment** reads **Captures** and writes **Notes** and **Topics** — never the reverse
- Only the user writes **Captures**; only the pipeline writes **Notes** and **Topics**
  (single-writer rule)
- One **Capture** yields exactly one **Note**; one **Topic** draws on many **Notes**
- A **Topic** may declare a parent **Topic**; hierarchy is metadata, never folder structure
- A **Capture** may cite one **Source**, supplied at capture time and never inferred
- A **Source** is auto-created; a Person, Organization or Concept needs **Registry** promotion
- A **Topic** exists only for an entity in the **Registry**; everything else stays a **Candidate**
- Only the user writes the **Registry**; only the pipeline writes **Candidates**
- A **Note** has exactly one **Kind** and any number of **Items**
- An **Item** is a proposal; accepting one creates a **Task** that outlives it
- A **Note** yields one **Contribution** per **Topic** it mentions; a **Topic** is assembled
  from its **Contributions**, never from the full text of its **Notes**
- Only **Notes** and **Topics** participate in search, backlinks and the graph
- A thought had while reading a **Note** becomes a new **Capture** referencing it, never an
  edit to that **Note** nor an amendment to the original **Capture**

## Example dialogue

> **Dev:** "You fixed a typo — do we re-run **Enrichment**?"
> **User:** "If I fixed it in the **Capture**, yes, that **Note** is now stale. If I fixed it
> in the **Note**, that's not something I'm allowed to do."

## Flagged ambiguities

- "note" was used loosely for both the dictated thing and the processed thing — resolved:
  the dictated thing is a **Capture**, only the derived artifact is a **Note**.
