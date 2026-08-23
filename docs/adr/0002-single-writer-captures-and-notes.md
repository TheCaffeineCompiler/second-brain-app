# Captures and Notes are single-writer artifacts

Enrichment and the user can touch the same material concurrently, and mixed-ownership
files make every such collision a real content conflict. Instead of designing conflict
resolution, we remove the possibility: the Vault holds two kinds of document, each with
exactly one writer. A **Capture** is raw and written only by the user; a **Note** is
derived and written only by the pipeline. Notes are a projection of Captures and can be
deleted and rebuilt at any time.

## Considered Options

- **Region ownership inside one file** — agents own frontmatter plus a delimited generated
  block, the user owns the prose. Keeps one file per thought, but forbids the pipeline from
  ever improving the note itself, and leaves a file with two writers.
- **Agents rewrite notes in place** — most capable, but every collision is an unmergeable
  content conflict and the user's original words can be altered or lost.

The two-artifact split was chosen because it gives the pipeline full freedom to rewrite,
restructure and clean up dictated prose while guaranteeing the user's original words are
never modified, and because conflicts become structurally impossible rather than handled.

## Consequences

Notes are regenerable, so improving the pipeline means replaying the corpus rather than
migrating data. Only Notes participate in search, backlinks and the graph — meaning the
pipeline's extraction quality determines what is discoverable.
