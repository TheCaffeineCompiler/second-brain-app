# Topics are flat files, hierarchy is metadata

Topic pages could plausibly be folders with an index file, letting a broad Topic hold
sub-pages. We store every Topic as a single flat file under `topics/` instead, and express
any hierarchy as a `parent` field in the Registry, rendered as nesting in the reading view.

Three reasons. **Membership is many-to-many**: a Note about using Claude at Acme belongs to
both `llm` and `acme`, and a single-parent folder cannot contain it — so a Topic folder
could never hold its Notes anyway. **Sub-pages need names**: if the pipeline invents
`topics/llm/prompting.md` it has invented an identifier, violating ADR-0004; and if
`prompting` is registered, it is not a sub-page but a Topic in its own right.
**Hierarchy is the most volatile structure in a knowledge base** — whether
`prompt-engineering` sits under `llm` or under `writing` is a judgement that changes often.
Folders make the path the identity, so every change of mind becomes a file move that breaks
inbound links; metadata makes it a one-line edit and a replay.

## Consequences

A Topic page is a **synthesis plus a link index, not a concatenation of every mention**.
The bulk of the content stays in Notes, so a Topic is large in fan-out and small in bytes.

A Topic becoming unwieldy is therefore not a file-size signal but a signal that its
synthesis has grown too coarse to be useful. The remedy is registering narrower Topics
through Candidate review, not splitting the file.

Nothing may refer to a Topic by path except the Registry, or renaming stops being cheap.
