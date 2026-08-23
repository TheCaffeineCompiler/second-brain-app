# The quality harness guards determinism, not just correctness

Standard linting, typing and unit tests apply and need no justification. This records the
parts that are specific to this system, where the usual harness does not reach.

**The pipeline's core is non-deterministic**, so two distinct mechanisms are needed and must
not be confused. **Cassettes** behind the `LanguageModel` port record and replay responses, so
tests are fully deterministic. **Evals** are separate: tests answer "did it break", evals
answer "did it get worse". Enrichment quality can degrade without a single test failing. Evals
run on their own cadence and must not gate CI.

**The golden-corpus replay test is the highest-value test in the system.** Fixed Captures plus
fixed cassettes must produce a byte-identical vault across runs. It guards ADR-0010's
stability claim directly, which is what stands between the user and a knowledge base that
churns every night. Alongside it, a **churn-budget test** adds one Capture to the golden corpus
and asserts the resulting diff touches only the expected files and stays within a line budget.

**Invariants are executable.** The ADRs are full of mechanically checkable rules, and these
matter more than generic architecture-test conventions: no pipeline code path writes to
`captures/` or `registry.md` (ADR-0002); derived paths are pure functions of their inputs
(ADR-0004); every markdown file carries parseable frontmatter with a non-empty `type`
(ADR-0015); and **a replay never modifies or deletes a decided artifact** (ADR-0011) — which
warrants a runtime guard as well as a test, being the one failure that loses data permanently.

**Cost is a tested property.** ADR-0010 claims nightly spend scales with the daily delta
rather than corpus size. Asserting token spend against a growing golden corpus keeps that
claim true.

## Operational

The scheduled job runs unattended, so each run writes a report — what changed, what it cost —
to `log.md`, which OKF reserves for chronological history and which Obsidian renders directly.

**The Vault repository is private and force-push is blocked.** Decided artifacts are
irreplaceable and Git history is their only backup.

**Semantic versioning applies to the pipeline for a non-obvious reason.** The pipeline version
is a domain input: ADR-0003 and ADR-0010 make it part of staleness, so bumping it triggers a
full corpus replay. It is versioned because the number is read by the system and carries a
cost, not as release ceremony.

## Sequencing

Executable invariants and repo protection are slice 1's definition of done, because the risk
of losing data exists the moment anything is written. Cassettes, the golden corpus and the
churn budget arrive with slice 2, when there is a corpus and a Topic layer to measure. Evals
and cost assertions arrive with the first scheduled run. Building the whole harness first
would repeat the mistake ADR-0018 avoids — heavy investment away from where the risk is.

## Local development

The stack runs offline via Docker Compose: a **bare Git repository in a volume** stands in for
GitHub over the filesystem — same protocol, no network or auth — seeded with a fixture vault
and a mounted working copy that can be opened in Obsidian while the pipeline runs against it.
`fake-gcs-server` stands in for the audio bucket, a stub adapter serves recorded LLM
responses, and Cloud Scheduler is replaced by a compose profile that invokes the job.
