# Git repository as system of record

The PRD requires markdown files that are portable and directly accessible to external
CLI tools and AI agents (§1), while also requiring deployment on Cloud Run (§7), which
has no durable filesystem. We resolve this by making a Git repository the single system
of record for all notes, and treating everything the app computes — search index, graph,
backlink candidates — as a disposable derived index that can be rebuilt from the repo at
any time.

## Considered Options

- **GCS bucket as system of record** — cloud-native and directly readable from Cloud Run,
  but offers no history, so an enrichment agent that corrupts notes overnight leaves no
  path back. Also narrows "accessible to external tools" to "tools that speak GCS".
- **Database as system of record, markdown as export** — fast queries and a trivial graph
  view, but directly contradicts the markdown-first requirement and makes the files a
  second-class artifact.

Git was chosen because portability, agent-accessibility and reversibility all fall out of
it structurally rather than being properties we have to maintain by hand.

## Consequences

Merge conflict handling becomes a designed feature rather than an edge case, since
overnight enrichment and human edits can touch the same note concurrently.
