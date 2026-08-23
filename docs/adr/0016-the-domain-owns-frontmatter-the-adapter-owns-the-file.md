# The domain owns the frontmatter contract, the adapter owns the file

Markdown-in-Git is the system of record (ADR-0001) in the OKF format (ADR-0015), which sits
awkwardly with the ports-and-adapters requirement in §7. Orthodox hexagonal would hold
domain objects and treat markdown as pure serialisation — but then the file stops being the
truth and the object graph becomes it, and OKF's requirement to preserve unknown frontmatter
keys when round-tripping fights a model that only knows the fields it declared.

We split it at the frontmatter line. The **domain** owns the frontmatter contract: it knows a
Note has a `source_hash`, a `kind` and Contributions, as structured typed values carrying
real rules. The **adapter** owns the file: that this is YAML at a path, with standard markdown
links, and that unknown keys are carried through opaquely without ever entering the model.
The body is content rather than structure — the domain treats it as an opaque blob it may
hand to the `LanguageModel` port but never parses.

## Considered Options

- **Orthodox: domain objects, markdown as serialisation** — textbook and fully testable
  without files, but round-tripping silently drops keys the model does not declare, breaking
  OKF conformance.
- **Document-centric: the domain manipulates markdown and YAML directly** — honest about what
  the system is, but leaves barely any domain model, with business rules doing string
  manipulation.

## Ports

`Vault` (Git/GitHub), `LanguageModel`, `Transcriber`, `KnowledgeIndex`, `SourceSuggester`
(assistive only, per ADR-0009), and `Clock`. The clock is a genuine port rather than a
utility: ADR-0004 makes Capture identity a timestamp, so an ambient clock would make
identities untestable and replays irreproducible.

## Consequences

**Paths are an adapter concern.** The domain refers to a Topic by its Registry name; only the
Vault adapter knows that becomes `topics/llm.md`. This is what makes ADR-0007's claim that
renaming is cheap actually true rather than aspirational.

**The domain cannot validate the body.** Malformed markdown is caught by the adapter or by a
test, never by a domain rule. This is deliberate — the alternative is a domain model that
owns a markdown parser.
