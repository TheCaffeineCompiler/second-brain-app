# Second Brain

A personal knowledge system. You dictate or type unstructured thoughts — mostly takeaways from
podcasts, blogposts and meetings — and an agentic pipeline turns them into a structured,
linked, searchable knowledge base. Everything is markdown in a Git repository, so the knowledge
outlives the app.

> **Status: the spine runs.** A Capture in a Git Vault is enriched into a Note and committed
> back, locally or in CI. Contributions and Topics are not built yet. Start with
> **[docs/design-overview.pdf](docs/design-overview.pdf)** — two pages covering the whole system —
> then **[docs/tutorials/enrichment.md](docs/tutorials/enrichment.md)** to run it yourself.

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

Captures, Notes and the Registry exist in code today. Contributions, Topics, Sources and
Candidates are designed but not yet built.

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
.env                        Committed configuration, read by both compose and the host CLI
docker-compose.yml          The whole stack, offline
apps/pipeline/
  src/pipeline/
    domain/                 Captures, Notes, enrichment, drift — no I/O, no SDKs
    adapters/               Git, GitHub, markdown, and one module per model provider
    cli.py                  init, enrich, list, show
  tests/                    78 tests, including executable architecture invariants
fixtures/vault/             The seed Vault the local stack clones from
scripts/quality_summary.py  Renders the CI quality page
docs/
  design-overview.pdf       Two-page overview of the whole design
  design-overview.html      Source for the above; regenerated as decisions land
  adr/                      24 architectural decisions, each with its rejected alternatives
  tutorials/enrichment.md   Run the pipeline end to end in five steps
  requirements/
    requirements.v000.md    The original PRD
    slice-1.md              Scope and definition of done for the tracer bullet
    post-mvp.md             Deliberately deferred work
```

**This repository is the application.** The Vault — the user's actual notes — lives in a
separate, private repository, created and protected by the application's `init` command rather
than by hand, and referenced through configuration. Initialization runs under a bootstrap
credential held locally; the runtime credential that reaches Cloud Run is scoped to the Vault
repository alone. See [ADR-0001](docs/adr/0001-git-repository-as-system-of-record.md),
[ADR-0019](docs/adr/0019-the-quality-harness.md) and
[ADR-0023](docs/adr/0023-the-vault-is-provisioned-by-an-init-command.md).

## Roadmap

The MVP has no app. Obsidian is the entire interface, and the review loops are just files you
move a line between — so the first release is a pipeline and nothing else, because that is
where all the risk lives ([ADR-0018](docs/adr/0018-the-mvp-has-no-app.md)).

| # | Slice | Proves | Status |
|---|---|---|---|
| 1 | Capture in Git → enrichment → Note committed back | The whole spine, end to end | Runs locally and in CI; not yet deployed as a scheduled job |
| 2 | Contributions → Topics, gated by a hand-written Registry | Whether Topic pages are worth reading | Next |
| 3 | `candidates.md` / `items.md` review loops | Whether promotion friction is tolerable | |
| 4 | Desktop hotkey and local Whisper, Registry-biased | Capture ergonomics | |
| 5 | Mobile share-target capture | Provenance at its cheapest moment | |
| 6 | PWA and client-side index | Only once Obsidian stops sufficing | |

Slices 1–3 are a decision point, not a milestone. If derived Topics turn out not to be useful,
the answer is to fix enrichment rather than proceed — and having built no app is what keeps
that cheap.

## Provisioning a Vault

The Vault is a separate private repository, created by the application rather than by
hand (ADR-0023):

```bash
pipeline init <owner>/second-brain-vault
```

This creates it private, applies branch protection, and seeds the skeleton — the Registry,
a README, `log.md` and the `captures/` region. It seeds **decided artifacts only**; the
derived regions appear when the pipeline first writes them. Running it again is safe: it
fills only what is absent and never overwrites.

`init` authenticates through your own `gh` login, which is the bootstrap credential — it is
never deployed. The runtime credential is separate and can only push, so nothing that
reaches Cloud Run is able to create or delete a repository.

> **Branch protection needs GitHub Pro on private repositories.** Without it, `init` warns
> that force-push is not blocked and continues. The code carries its own guard — no module
> may pass `--force` to git, asserted as an executable invariant.

## Running the pipeline

```bash
pipeline enrich          # derive a Note for every Capture that needs one, and commit them
pipeline list            # every Capture in the Vault
pipeline show <id>       # one Capture
```

`enrich` is idempotent. It reads every Capture, skips the ones whose Note is already current,
and commits the rest in a single commit under its own identity. Three things make a Note need
deriving again: the Capture changed, the pipeline version changed, or the Note is missing.
Nothing about it depends on a timestamp, so a replay of the whole corpus produces the same
result as the runs that built it incrementally.

If you hand-edit a Note, the pipeline notices — the content hash no longer matches — and
refuses to overwrite it rather than silently discarding your edit. Notes are derived; the
place to record a thought about one is a new Capture ([ADR-0003](docs/adr/0003-notes-are-read-only-with-drift-detection.md)).

[docs/tutorials/enrichment.md](docs/tutorials/enrichment.md) walks the whole thing through in
five steps; the first four need no API key.

## Local development

The stack runs entirely offline. A bare repository stands in for GitHub over the filesystem —
same protocol, no network, no auth.

```bash
docker compose up --build          # seeds .vault-remote/vault.git from fixtures/vault
```

Configuration lives in a committed `.env` at the project root, read by both docker compose
and the host CLI, so there is nothing to export. **Secrets and machine-specific choices go
in `.env.local`**, which is gitignored and overrides `.env`:

```bash
cat > .env.local <<'ENV'
LLM_PROVIDER=openai
LLM_MODEL=llama3.1
LLM_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=...
ENV
```

A test asserts `.env` holds nothing that looks like a secret, because a key put in the
wrong file is published to everyone who clones the repo and the file cannot tell you so.


```bash
docker compose run --rm pipeline list      # in the container
uv run --package pipeline pipeline list    # on the host, from anywhere in the repo
```

The paths in `.env` are **relative to the project root**, which is what lets one value be
correct both inside the container and outside it — the Vault is mounted at the same position
relative to the working directory in each. Real environment variables always take precedence,
so deployment sets no file at all.

`.working-copy/vault` is a normal working copy — open it in Obsidian while the pipeline runs
against it. Re-running `docker compose up` never re-seeds an existing Vault; initialization is
not destructive (ADR-0023).

## Choosing a language model

Enrichment is not tied to one vendor (ADR-0024). Set the provider through the
environment:

```bash
export LLM_PROVIDER=anthropic                      # the default
export ANTHROPIC_API_KEY=sk-ant-...

export LLM_PROVIDER=openai                         # any OpenAI-compatible endpoint
export LLM_MODEL=llama3.1                          # Ollama, locally
export LLM_BASE_URL=http://localhost:11434/v1

pipeline enrich --provider stub                    # offline and deterministic
```

Both providers are sent the same prompt and the same JSON schema, so a switch
changes who answers rather than what was asked. Schema adherence varies a great
deal between models — a reply that ignores the schema fails loudly rather than
being repaired, because patching one silently would put invented content into the
Vault under your name.

The provider is part of the pipeline version, so switching re-derives the corpus.

## Quality

Every push runs the gates in [ADR-0019](docs/adr/0019-the-quality-harness.md): ruff, `ruff
format --check`, mypy in strict mode, and the test suite with coverage. CI renders a **quality
page** into the job summary, grouping tests by what they guard rather than by file, so a
failure says which property broke.

Some of the tests are architecture invariants, asserted against the AST rather than by
convention — the domain never touches the filesystem, never imports an adapter, and never
imports a provider SDK; no adapter imports more than one provider SDK; no module passes
`--force` to git; `.env` holds nothing resembling a secret and `.env.local` is untracked.
Each has been mutation-checked, because an invariant that cannot fail is decoration.

There is also an end-to-end test that runs the real stack — compose seeds a Vault, the
container reads it, and the host CLI reads the same Vault with nothing exported. It exists
because that last case broke once and was invisible to every unit test.

## Stack

Markdown in Git, in Google's [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md).
Python 3.12 in a `uv` workspace. Ports and adapters throughout, with the domain owning the
frontmatter contract and adapters owning the files ([ADR-0016](docs/adr/0016-the-domain-owns-frontmatter-the-adapter-owns-the-file.md)).
The pipeline is designed to run as a Cloud Run Job on GCP ([ADR-0013](docs/adr/0013-compute-is-split-by-workload.md));
that deployment is not built yet.

## Reading the decisions

The ADRs in `docs/adr/` are the real documentation. Each records what was decided, what was
rejected, and why. The ones that explain the most:

- [0002 — Captures and Notes are single-writer artifacts](docs/adr/0002-single-writer-captures-and-notes.md)
- [0004 — Derived documents never invent identifiers](docs/adr/0004-derived-documents-never-invent-identifiers.md)
- [0010 — Topic synthesis is map-reduce over cached Contributions](docs/adr/0010-topic-synthesis-is-map-reduce-over-cached-contributions.md)
- [0011 — Every artifact is either derived or decided](docs/adr/0011-every-artifact-is-either-derived-or-decided.md)
