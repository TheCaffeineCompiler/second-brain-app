# Notes are read-only, enforced by drift detection

The single-writer rule is only an invariant if something enforces it; nothing in Obsidian
stops the user editing a derived Note, and the next pipeline run would silently overwrite
it. Every Note therefore carries a `source_hash` of the Captures it was derived from and a
`content_hash` of itself. Before regenerating, the pipeline verifies the Note still matches
its own `content_hash`; a mismatch means the user edited it, and the pipeline refuses to
overwrite and flags the Note for resolution rather than destroying the edit.

The same hashes determine staleness. Note that an enrichment *timestamp* — as originally
specified in the PRD — can only record when a Note was last processed, never whether it
needs processing again. A Note is stale when its `source_hash` no longer matches its
Captures, or when the pipeline version has moved on. Timestamps remain useful for
observability, not for scheduling work.

## Consequences

The user cannot annotate a Note in place. A thought had while reading becomes a **new
Capture that references the Note**, never an amendment to the original Capture — amending
would rewrite history and break the promise that Captures are unedited. Surfacing this as
a first-class affordance is deferred past MVP; see `docs/requirements/post-mvp.md`.
