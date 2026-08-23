# The language model provider is configuration, not architecture

Enrichment must not tie the Vault to one vendor. The `LanguageModel` port already
made that possible in principle, but a port with a single implementation is a
guess: nothing had ever exercised it as an abstraction, so nothing proved the
domain was actually provider-neutral. The same weakness appeared earlier with the
`Vault` port, which no module imported until it was annotated against.

A second adapter now exists. Enrichment runs against **Anthropic** or against any
**OpenAI-compatible endpoint** — one adapter covering Ollama and LM Studio locally,
and OpenRouter, Together, vLLM and OpenAI remotely. Which one runs is read from
`LLM_PROVIDER` at startup (12-factor), with provider-specific settings read inside
their own branch so nothing outside that module knows Anthropic has an effort
ladder and OpenAI has a base URL.

Local endpoints matter for the reason local transcription does (ADR-0017):
otherwise every Capture is sent to a third party on its way into the Vault.

## The prompt and schema are shared, the request shapes are not

Both adapters ask for the same thing — one system prompt, one JSON schema, one
validator — so a provider switch changes who answers rather than what was asked,
and outputs stay comparable. Only the request shape differs: Anthropic takes
`output_config.format`, OpenAI-compatible endpoints take `response_format`.

## Consequences

**Provider independence is asserted, not promised.** No domain module may import a
provider SDK, and no adapter may import more than one — both checked over the
source, so choosing one provider never requires another's SDK or credentials.

**The provider is part of the pipeline version.** Two providers are not
interchangeable outputs, so switching marks the corpus stale and re-derives it.
That is correct rather than unfortunate: the Notes really did change.

**Schema adherence varies far more than capability does.** Many endpoints accept
`response_format` and then ignore it, and small local models are notably worse at
it. The shared validator therefore fails loudly rather than repairing a bad reply —
silently patching one would put invented or truncated content into the Vault under
the author's name.

**Provider-agnostic does not mean quality-agnostic.** A local model is a genuine
privacy option, not an equivalent one; the enrichment it produces should be judged
before trusting it with the corpus.
