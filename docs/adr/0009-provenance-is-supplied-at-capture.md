# Provenance is supplied at capture, never inferred

The PRD has the pipeline web-search its way to a source URL from a casual mention (§3). That
fails in a way that is invisible: "that Huberman episode about sleep latency" resolves to a
plausible but wrong episode, and the takeaway is silently attributed to material the user
never consumed. Consistent with ADR-0005's refusal to guess at contextual references, we take
provenance from the user at capture time instead.

Capture carries an optional source field. It is filled by the **OS share sheet** rather than
typed — the user is already inside a podcast player or browser when the thought lands, so
sharing into the app supplies the URL at no friction cost. This makes the mobile app a
*share-target* app rather than a capture app, which is a materially different build from what
§2 describes. On desktop the hotkey capture prefills the field when the clipboard holds a URL.

## The unresolved state

Falling back to the Capture's own timestamp whenever no URL is given would conflate three
different situations. It is correct for a `meeting` (a real source with no URL) and for a
`thought` (genuinely self-originated). It is wrong when the Kind implies an external source
and the user simply forgot to share: that silently asserts the thought was self-originated,
and several takeaways from one episode become several distinct Sources that never aggregate.

So when the Kind implies an external source and none was supplied, the Note records
`source: unresolved` and joins a fill-in-later list, following the same review-list pattern as
Candidates. Timestamp identity applies only where the Capture genuinely *is* the source.

## Consequences

Web search survives from §3 in a reduced role: it may **suggest** matches for unresolved
sources for one-click confirmation. It may never apply one automatically.
