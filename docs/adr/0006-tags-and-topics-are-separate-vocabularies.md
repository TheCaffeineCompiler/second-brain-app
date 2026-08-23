# Tags and Topics are separate vocabularies

The PRD asks for automated tagging governed by a reference folder (§3) and for entity
extraction into People, Organizations, Concepts and Sources (§4), without saying whether
these are one system or two. They are two, and conflating them is the actual cause of the
tag sprawl §3 sets out to prevent.

A **Topic** is a subject a Capture is *about*. Its vocabulary is open-ended, it is governed
by the Registry, new ones arrive through Candidate review, and it is written as a wikilink.
A **Tag** is a facet of the note *itself* — its kind or status. It has no page, it is drawn
from a small closed enum the pipeline may select from but never extend, and it is written
as `#todo`.

Subjects grow without limit; facets should almost never grow at all. Giving them one
mechanism forces a single policy onto two opposite growth patterns.

## Consequences

Facet sprawl is impossible by construction, because a closed enum cannot grow on its own.
Subject sprawl is handled by human promotion instead.

**Extending the facet enum is a deliberate product decision, and should feel heavy.** If the
pipeline may propose new facets, the set stops being closed and sprawl returns.

The graph in §6 shows subject relationships rather than being dominated by every note
linking to `#idea`. This also matches idiomatic Obsidian use — links for subjects, tags for
states.

## Amendment

The detail that Topics are written as `[[wikilinks]]` is superseded by ADR-0015: they are
written as standard markdown links, per the OKF specification. The substance of this decision
— two vocabularies with opposite growth patterns — is unaffected.
