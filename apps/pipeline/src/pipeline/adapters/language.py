"""Choosing a language model provider.

Which provider runs enrichment is configuration, not architecture (12-factor).
The domain depends on the `LanguageModel` port and never learns who answered —
which is asserted, not assumed: see `test_the_domain_never_imports_a_provider`.

Provider-specific settings are read inside their own branch, so nothing outside
this module needs to know that Anthropic has an effort ladder and OpenAI has a
base URL.
"""

import os
from typing import cast

from pipeline.domain.language import LanguageModel

PROVIDERS = ("anthropic", "openai", "stub")
DEFAULT = "anthropic"


class UnknownProvider(RuntimeError):
    pass


def from_environment(provider: str | None = None) -> LanguageModel:
    """Build the configured provider.

    Imports are local so that choosing one provider never requires the others'
    SDKs to be installed or their credentials to be present.
    """
    choice = provider or os.environ.get("LLM_PROVIDER", DEFAULT)

    if choice == "stub":
        from pipeline.adapters.stub_language import StubLanguageModel

        return StubLanguageModel()

    if choice == "anthropic":
        from pipeline.adapters.claude import MODEL, ClaudeLanguageModel, Effort

        return ClaudeLanguageModel(
            model=os.environ.get("LLM_MODEL", MODEL),
            effort=cast(Effort, os.environ.get("ANTHROPIC_EFFORT", "low")),
        )

    if choice == "openai":
        from pipeline.adapters.openai_compatible import OpenAICompatibleLanguageModel

        model = os.environ.get("LLM_MODEL")
        if not model:
            raise UnknownProvider(
                "LLM_MODEL is required for the openai provider — there is no sensible\n"
                "default across OpenAI, OpenRouter, Ollama and the rest.\n\n"
                "  Locally, via Ollama:\n"
                "    export LLM_PROVIDER=openai LLM_MODEL=llama3.1\n"
                "    export LLM_BASE_URL=http://localhost:11434/v1"
            )
        return OpenAICompatibleLanguageModel(model=model, base_url=os.environ.get("LLM_BASE_URL"))

    raise UnknownProvider(f"'{choice}' is not one of {list(PROVIDERS)} — set LLM_PROVIDER")
