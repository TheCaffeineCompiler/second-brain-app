# Slice 1 — the tracer bullet

One Capture in Git, through a Cloud Run Job, back as a committed Note. It touches every
architectural layer once and produces something readable the same evening.

## In scope

- A Capture typed by hand into `captures/` and pushed (per ADR-0017, typing is the day-one
  capture path — no hotkey, no Whisper, no mobile app).
- A Cloud Run Job, triggered manually, that clones the Vault, selects Captures whose Note is
  missing or stale, derives each Note through the `LanguageModel` port, and commits back.
- The derived Note is OKF-conformant (ADR-0015): non-empty `type`, plus `generated: {by, at}`,
  `source_hash`, `content_hash` and `kind`.
- Staleness computed from `source_hash` and pipeline version — never a timestamp (ADR-0003).
- Drift detection: a Note whose `content_hash` no longer matches is flagged, not overwritten.

## Explicitly out of scope

Topics, Contributions, the Registry, Candidates, Items, the index, and any app. Slice 1 proves
the spine, not the knowledge model.

## Definition of done

- [ ] Running the job twice over an unchanged Vault produces **no commit at all** — the
      clearest possible proof that staleness works.
- [ ] Editing a Capture and re-running regenerates exactly that one Note.
- [ ] Hand-editing a Note and re-running refuses to overwrite it and reports it.
- [ ] Executable invariants green (ADR-0019): no write path touches `captures/`, derived paths
      are pure functions of their inputs, every markdown file carries a non-empty `type`.
- [ ] Vault repository is private and force-push is blocked on the default branch.
- [ ] `docker compose up` runs the whole flow offline against a bare repo in a volume, with a
      working copy openable in Obsidian.
- [ ] The run writes a report to `log.md`.

## Why this order

The first two checks are the ones worth building toward. Together they prove the pipeline is
incremental and idempotent, which is the property every later slice depends on and the hardest
one to retrofit.
