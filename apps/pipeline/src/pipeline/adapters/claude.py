"""Claude implementation of the LanguageModel port.

Provider-specific notes, none of which reach the domain:

- `temperature`, `top_p` and `top_k` are rejected on Claude Opus 5. There is no
  sampling knob, so no provider-independent determinism setting exists either —
  reproducible tests come from recorded responses instead (ADR-0019).
- Thinking is on by default, and `max_tokens` bounds thinking *plus* the response.
- Structured output goes through `output_config.format`; assistant prefills are
  rejected on this model.
"""

from typing import Literal

import anthropic
from anthropic.types import OutputConfigParam

from pipeline.adapters.enrichment_schema import CONTRACT, SCHEMA, SYSTEM, parse
from pipeline.domain.document import Document
from pipeline.domain.language import Enrichment

MODEL = "claude-opus-5"
MAX_TOKENS = 16000

# Opus 5 performs unusually well at low effort, and this is a cleanup task rather
# than a reasoning one — so low is the starting point, not a compromise.
type Effort = Literal["low", "medium", "high", "xhigh", "max"]


class Refused(RuntimeError):
    """Claude's safety classifiers declined the Capture."""


class ClaudeLanguageModel:
    def __init__(
        self,
        model: str = MODEL,
        effort: Effort = "low",
        client: anthropic.Anthropic | None = None,
    ) -> None:
        self._client = client or anthropic.Anthropic()
        self._model = model
        self._effort: Effort = effort

    @property
    def version(self) -> str:
        return f"anthropic-{self._model}-{self._effort}-{CONTRACT}"

    def enrich(self, capture: Document) -> Enrichment:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM,
            output_config=OutputConfigParam(
                effort=self._effort,
                format={"type": "json_schema", "schema": SCHEMA},
            ),
            messages=[{"role": "user", "content": capture.body}],
        )
        # A refusal arrives as HTTP 200 with content empty or partial, so the stop
        # reason has to be checked before indexing into it.
        if response.stop_reason == "refusal":
            raise Refused(f"the capture was declined: {response.stop_details}")

        return parse(next(block.text for block in response.content if block.type == "text"))
