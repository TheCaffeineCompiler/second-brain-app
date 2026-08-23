# The Vault is an OKF bundle, and links are standard markdown

The PRD names Open Knowledge Format in §1 without pinning it to anything. It is a real Google
Cloud specification — v0.1 in June 2026, v0.2 in July — that formalises precisely this
pattern: a directory of markdown files with YAML frontmatter, in Git, readable both by `cat`
and by an agent. We adopt it as the Vault's on-disk format.

Adoption is close to free, because the spec is deliberately permissive. `type` is the only
required field, values are not centrally registered, and consumers must tolerate unknown ones
— so `type: capture | note | topic | source | task` conforms as written, and `type` does
exactly the routing job our artifact classes need. Additional keys are explicitly allowed and
must be preserved when round-tripping, so `source_hash`, `content_hash`, `kind` and `parent`
are all legal. Two spec fields align with decisions already made: `generated: {by, at}` is the
derived/decided split of ADR-0011, and `sources:` with a required `resource` URI is the
provenance model of ADR-0009 almost field-for-field.

## Links are standard markdown, not wikilinks

The spec is explicit that OKF uses standard markdown links rather than `[[wikilinks]]`, which
conflicts with ADR-0006. We follow the spec. The usual argument for wikilinks is authoring
ergonomics — `[[` autocomplete — but under ADR-0002 and ADR-0003 links appear only in derived
artifacts written by the pipeline, so that authoring action never happens. Obsidian counts
standard markdown links in its graph and backlink panel regardless, so almost nothing is lost
and the links now resolve on GitHub and for any external agent, which is what §1 was actually
asking for.

## Consequences

**`stale_after` is deliberately omitted.** OKF offers a time-based staleness field, but
ADR-0003 makes staleness a content hash plus pipeline version, precisely because a timestamp
cannot say whether work needs doing. Populating it would mean something different to us than
to a reader of the spec.

**Nothing load-bearing may depend on the spec holding still.** It is a draft moving quickly.
The risk is bounded because we are labelling with OKF rather than building on it — every field
we need is ours regardless, and conformance costs one required key.
