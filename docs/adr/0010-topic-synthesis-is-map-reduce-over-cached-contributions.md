# Topic synthesis is map-reduce over cached Note contributions

A Topic is derived from every Note that mentions it, so a single new Capture invalidates
every Topic it touches. Re-synthesizing each affected Topic from all its Notes fails three
ways: cost grows with corpus size times daily activity, latency grows without bound, and —
worst — an LLM re-summarizing from scratch writes different prose each run, so every night
produces large diffs that reflect no actual change in the user's knowledge. That reduces Git
history to noise and silently rewords pages the user has already read, undoing the main
benefit of ADR-0001.

Enrichment is therefore split into a cached map step and a cheap reduce step. Each Note
extracts its **Contributions** — the few structured claims it makes about each Topic it
mentions. Extraction is 1:1 with the Note and a Note never changes once derived, so
Contributions are cached permanently. A Topic page is assembled from those short
Contributions, never from the full text of its Notes.

## Considered Options

- **Full re-synthesis on any change** — always coherent, but incurs all three failures above.
- **Append to the link index, re-synthesize the prose only occasionally** — cheap and stable,
  but leaves the synthesis, which is the entire value of a Topic, permanently stale.

## Consequences

**Nightly cost scales with what was captured that day, not with the size of the corpus.**
Without this the scheduled run in §5 gets slower every week until it stops finishing.

Churn is controllable: the Contribution set is hashed, and synthesis re-runs only when that
set actually changed. A Note that mentions a Topic in passing without adding a claim produces
no diff at all.

Contributions double as the link index the Topic page needs anyway.

**Pipeline version participates in staleness.** Changing an extraction prompt invalidates
every cached Contribution and requires a full corpus replay. This must be a deliberate,
visible, resumable operation with an observable cost — never something that silently starts
at 3am.

**A full replay cannot run inside an HTTP request.** Corpus-wide re-extraction takes hours,
so scheduled work is a Cloud Run **Job**, not a request handler on a Cloud Run service, and
must be resumable because a long replay will be interrupted.
