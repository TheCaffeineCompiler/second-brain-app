# Testing enrichment

How to drive the pipeline end to end and see for yourself that it does what the
ADRs claim. Steps 1–4 need no API key and no network. Step 5 needs both.

## 1. Start the stack

```bash
docker compose down -v && rm -rf .working-copy .vault-remote   # clean slate
docker compose up --build
```

This seeds `.vault-remote/vault.git` from `fixtures/vault/` and checks it out at
`.working-copy/vault`. Open that directory in Obsidian if you want to watch the
Notes appear as they are written.

## 2. Derive Notes, with no model involved

`--model stub` runs a deterministic fake instead of Claude, so this works offline
and produces the same output every time.

```bash
cd apps/pipeline
uv run pipeline enrich --provider stub
```

```
2 derived, 0 unchanged
```

Look at what it wrote:

```bash
cat ../../.working-copy/vault/notes/2026-08-23T1714.md
```

```markdown
---
type: note
title: Kickoff with Acme. They want the migration done before their
kind: meeting
generated:
  by: second-brain-pipeline@stub-1
  at: '2026-08-23T17:12:32+00:00'
source_hash: 560fc309d7609987
content_hash: f2ec00ec98f5cd37
---
```

The title is bad on purpose — the stub just truncates the first line. That is the
point of the stub: it exercises the whole path without pretending to be good, so a
bad title here is the harness working, not enrichment failing.

`source_hash` is a hash of the Capture; `content_hash` is a hash of this Note. Those
two fields are what steps 3 and 4 test.

## 3. Prove the run is incremental

```bash
uv run pipeline enrich --provider stub
```

```
0 derived, 2 unchanged
```

**No commit was made at all.** This is the property everything else rests on: nightly
cost scales with what you captured that day, not with how much you have ever captured
(ADR-0010). Confirm nothing landed:

```bash
git -C ../../.working-copy/vault log --oneline
```

Now change a Capture and watch exactly one Note regenerate:

```bash
echo "Correction: the audit is in October, not November." \
  >> ../../.working-copy/vault/captures/2026-08-23T1714.md
uv run pipeline enrich --provider stub     # → 1 derived, 1 unchanged
```

## 4. Prove the pipeline refuses to overwrite your edits

Edit a Note by hand — the thing the single-writer rule forbids and that nothing in
Obsidian prevents:

```bash
echo "A sentence I added myself." >> ../../.working-copy/vault/notes/2026-08-23T1714.md
uv run pipeline enrich --provider stub
```

```
0 derived, 1 unchanged, 1 edited by hand and left alone
  edited by hand, left alone: 2026-08-23T1714
```

Two things to check, and the second matters more than the first:

```bash
tail -1 ../../.working-copy/vault/notes/2026-08-23T1714.md   # your sentence is still there
git -C ../../.working-copy/vault log --format='%an: %s' -3   # your edit was NOT committed
```

The pipeline detected the drift, refused to overwrite, reported it, and **did not
commit your text under its own identity**. It stages only the files it wrote.

## 5. Run it against a real model

This is the step I could not verify — it needs credentials or a local server.

**Anthropic** (the default provider):

```bash
export ANTHROPIC_API_KEY=sk-ant-...     # or run `ant auth login`
uv run pipeline enrich
```

**Locally, with Ollama** — nothing leaves your machine:

```bash
ollama serve && ollama pull llama3.1
export LLM_PROVIDER=openai LLM_MODEL=llama3.1 LLM_BASE_URL=http://localhost:11434/v1
uv run pipeline enrich
```

**Any other OpenAI-compatible endpoint** — OpenRouter, Together, vLLM, OpenAI —
is the same three variables with a different `LLM_BASE_URL`.

Force a full re-derivation first, so there is work to do:

```bash
rm -rf ../../.working-copy/vault/notes && uv run pipeline enrich
```

Read the result and judge it — this is the question ADR-0018 says the whole project
rests on:

```bash
cat ../../.working-copy/vault/notes/*.md
```

**Is a derived Note actually better than the raw Capture?** Specifically:

- Is the **title** something you would recognise in a list a year from now?
- Is the **body** cleaned up without anything invented? Compare it against the
  Capture line by line — the prompt forbids adding facts, and this is where you find
  out whether that holds.
- Is `kind` right? It is inferred from the content alone, deliberately ignoring the
  Capture's own `kind` field, because disagreement between the two is how missing
  provenance gets detected (ADR-0009).

If the answers are no, the fix is the prompt in `apps/pipeline/src/pipeline/adapters/claude.py`
— not more scaffolding around it.

Expect a small local model to be noticeably worse here, and to fail with `Malformed`
where a frontier model succeeds — many endpoints accept a JSON schema and then ignore
it. That failure is deliberate: repairing a bad reply would put invented or truncated
content into the Vault under your name.

### Effort and cost

On Anthropic, effort defaults to `low`. Opus 5 performs unusually well there and this
is a cleanup task rather than a reasoning one, so `low` is a starting point rather than
a compromise. Try raising it and see whether the output actually improves:

```bash
ANTHROPIC_EFFORT=medium uv run pipeline enrich
```

### Anything that changes the output re-derives the corpus

The pipeline version covers the provider, the model, the effort level and a hash of the
prompt. Change any of them and **every Note is re-derived** — correct, because the Notes
really did change, but it means a sweep costs a full pass each time.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `VAULT_REMOTE is not set` | Run from inside the repo, after `docker compose up` — config comes from `.env` |
| `git pull --rebase failed` | Should not happen: a dirty working copy is expected and the pull is skipped. If it does, the working copy has a conflict — resolve it in the Vault |
| Everything re-derives unexpectedly | The pipeline version changed. It covers the provider, model, effort and a hash of the prompt — editing any of them invalidates the corpus by design |
| `Malformed` | The model ignored the JSON schema. Common on small local models; try a larger one rather than loosening the validator |
| `LLM_MODEL is required` | The `openai` provider has no default model — OpenAI, OpenRouter and Ollama share no sensible one |
| `Refused` | Claude's safety classifiers declined the Capture. Returns HTTP 200, not an error, which is why the adapter checks `stop_reason` before reading content |
