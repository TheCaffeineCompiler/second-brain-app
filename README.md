# Second Brain

A personal knowledge system. You dictate or type unstructured thoughts — mostly takeaways from
podcasts, blogposts and meetings — and an agentic pipeline turns them into a structured,
linked, searchable knowledge base. Everything is markdown in a Git repository, so the knowledge
outlives the app.

> **Status: design.** No code yet. This repository currently holds the domain model, the
> architectural decisions behind it, and the implementation plan. Start with
> **[docs/design-overview.pdf](docs/design-overview.pdf)** — two pages covering the whole system.

## The organising idea

Every artifact is either **derived** or **decided**.

**Derived** artifacts are pipeline-owned, disposable, and rebuilt from scratch at will.
**Decided** artifacts are human-owned, durable, and never regenerated. Nothing is both, and the
combination the model deliberately has no room for is decided state living inside a derived
artifact. Almost every rule in the system follows from that split.

| Artifact | What it is | | Identity from |
|---|---|---|---|
| **Capture** | A raw thought as you recorded it, unedited by the system | decided | Timestamp |
| **Registry** | Canonical entity names and aliases — the naming authority | decided | You |
| **Task** | An Item you accepted — outlives the Note it came from | decided | Its own |
| **Note** | A cleaned, tagged, linked document derived from one Capture | derived | Its Capture |
| **Contribution** | The few claims one Note makes about one Topic — the cached unit | derived | Note + Topic |
| **Topic** | A synthesis of what you know about one entity, plus a link index | derived | Registry name |
| **Source** | Where a Capture came from: podcast, blogpost, book, meeting | derived | URL (external) |
| **Candidate** | An entity the pipeline noticed that you haven't admitted yet | derived | — |

Full definitions and relationships are in **[CONTEXT.md](CONTEXT.md)**.

## How it works

```
Source (share sheet)                                   Registry gates
        ↓                                                    ↓
    Capture  ──→  Enrich  ──→  Note  ──→  Contribution  ──→  Topic
        ↑                                                    │
        └──── a thought while reading comes back as a new Capture, never an edit
```

Nightly, new Captures sync, Notes are derived, Contributions are extracted and cached, and only
Topics whose Contribution set actually changed are re-synthesised. Cost scales with what you
captured that day, never with the size of the corpus.

### The load-bearing rules

- **One writer per artifact.** You write Captures and the Registry; the pipeline writes
  everything else. Conflicts are impossible rather than resolved.
- **Nothing invents an identifier.** A Note inherits its Capture's identity, a Topic its
  Registry name, a Source its URL. Anything an LLM would have to name freely is forbidden,
  because it drifts between runs and rots every link.
- **Never guess — leave it unresolved.** A wrong entity match or source URL is silent and
  permanent; an unresolved mention is visible and harmless.
- **Derived artifacts are disposable.** Improving the pipeline is a replay, never a migration.
- **Staleness is a hash, not a timestamp.** A timestamp records when work happened; only a
  content hash plus pipeline version says whether it needs doing again.
- **Decided state never lives on a derived artifact**, or the next replay destroys it.

## Repository layout

```
CONTEXT.md                  Domain glossary and relationships
README.md                   You are here
docs/
  design-overview.pdf       Two-page overview of the whole design
  design-overview.html      Source for the above; regenerated as decisions land
  adr/                      22 architectural decisions, each with its rejected alternatives
  requirements/
    requirements.v000.md    The original PRD
    slice-1.md              Scope and definition of done for the tracer bullet
    post-mvp.md             Deliberately deferred work
```

**This repository is the application.** The Vault — the user's actual notes — lives in a
separate, private repository. That separation is deliberate: see
[ADR-0001](docs/adr/0001-git-repository-as-system-of-record.md) and
[ADR-0019](docs/adr/0019-the-quality-harness.md).

## Roadmap

The MVP has no app. Obsidian is the entire interface, and the review loops are just files you
move a line between — so the first release is a pipeline and nothing else, because that is
where all the risk lives ([ADR-0018](docs/adr/0018-the-mvp-has-no-app.md)).

| # | Slice | Proves |
|---|---|---|
| 1 | Capture in Git → Cloud Run Job → Note committed back | The whole spine, end to end |
| 2 | Contributions → Topics, gated by a hand-written Registry | Whether Topic pages are worth reading |
| 3 | `candidates.md` / `items.md` review loops | Whether promotion friction is tolerable |
| 4 | Desktop hotkey and local Whisper, Registry-biased | Capture ergonomics |
| 5 | Mobile share-target capture | Provenance at its cheapest moment |
| 6 | PWA and client-side index | Only once Obsidian stops sufficing |

Slices 1–3 are a decision point, not a milestone. If derived Topics turn out not to be useful,
the answer is to fix enrichment rather than proceed — and having built no app is what keeps
that cheap.

## Stack

Markdown in Git, in Google's [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md).
Pipeline as a Cloud Run Job on GCP. Ports and adapters throughout, with the domain owning the
frontmatter contract and adapters owning the files.

## Reading the decisions

The ADRs in `docs/adr/` are the real documentation. Each records what was decided, what was
rejected, and why. The ones that explain the most:

- [0002 — Captures and Notes are single-writer artifacts](docs/adr/0002-single-writer-captures-and-notes.md)
- [0004 — Derived documents never invent identifiers](docs/adr/0004-derived-documents-never-invent-identifiers.md)
- [0010 — Topic synthesis is map-reduce over cached Contributions](docs/adr/0010-topic-synthesis-is-map-reduce-over-cached-contributions.md)
- [0011 — Every artifact is either derived or decided](docs/adr/0011-every-artifact-is-either-derived-or-decided.md)
