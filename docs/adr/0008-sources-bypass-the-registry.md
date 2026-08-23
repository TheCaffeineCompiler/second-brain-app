# Sources bypass the Registry

ADR-0005 routes every entity through Candidate review before it can become a Topic. Applied
to Sources that is unworkable: the user's Captures are overwhelmingly takeaways from
podcasts, blogposts and meetings, so review would mean confirming eight or more entities a
week purely to attribute material whose origin is already known. A review list that large is
abandoned, and once abandoned the Registry stops being the naming authority and ADR-0005
collapses in general.

The reason ADR-0005 needs a human is that an entity's canonical name is a *judgement* —
"Huberman" versus "Andrew Huberman" versus "Dr. Andrew Huberman" — and an LLM making that
call yields unstable identity. A URL is not a judgement; it is an identifier the world has
already assigned. We therefore split entity types by where identity originates:

- **Source** — identity is external (URL, ISBN, episode GUID). Auto-created without review.
  Nothing is invented, so ADR-0004 holds. Two Captures citing the same URL deterministically
  resolve to the same Source.
- **Person, Organization, Concept** — identity is a judgement. Registry and Candidate review
  as per ADR-0005.

## Consequences

Review burden falls to the entities that genuinely need human judgement, which is what keeps
the Candidate list small enough to actually be worked through.

Meetings are provenance without an external identifier. They take the Capture's own
timestamp as identity rather than letting the pipeline name them `acme-kickoff`, which would
be an invented identifier. The value in a meeting is its attendees, who are Registry-governed
People.
