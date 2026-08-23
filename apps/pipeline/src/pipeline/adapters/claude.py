"""Claude implementation of the LanguageModel port.

Notes on the API shape, because several of these are not obvious:

- `temperature`, `top_p` and `top_k` are rejected on Claude Opus 5. There is no
  sampling knob, so a real model cannot be pinned for determinism — which is why
  reproducible tests come from recorded responses instead (ADR-0019).
- Thinking is on by default, and `max_tokens` bounds thinking *plus* the response,
  so the budget needs headroom well beyond the size of the answer.
- Structured output is requested through `output_config.format`, not by prefilling
  an assistant turn — prefills are rejected on this model.
"""

import json
from hashlib import sha256
from typing import Any, Literal

import anthropic
from anthropic.types import OutputConfigParam

from pipeline.domain.document import Document
from pipeline.domain.kind import Kind
from pipeline.domain.language import Enrichment

MODEL = "claude-opus-5"
MAX_TOKENS = 16000

SYSTEM = """You clean up dictated notes for a personal knowledge base.

The text you receive was spoken aloud and transcribed, so it rambles, repeats
itself, and contains false starts. Turn it into something the author will want to
reread in a year.

Rules, in order of importance:

1. Never add anything the author did not say. No invented facts, sources, names,
   figures or conclusions. If a thought is unfinished, leave it unfinished. You
   are editing, not writing.
2. Keep the author's voice, opinions and hedging. "I think maybe" stays uncertain.
3. Remove transcription noise: filler words, restarts, repeated phrases, and
   artefacts of speaking rather than writing.
4. Give it structure only where the content already has it. Do not impose headings
   or bullet lists on a single continuous thought.
5. Write a title that says what this note is actually about — not a category, and
   not the first sentence restated.

Choose the `kind` from what the note itself says, not from any metadata:
  podcast  — a takeaway from something the author listened to
  article  — a takeaway from something the author read
  meeting  — notes from a conversation the author took part in
  thought  — the author's own thinking, not prompted by a specific source

Judge `kind` on the content alone. Getting this wrong in either direction is
worse than useless: it is how the system detects that provenance went missing."""

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "kind": {
            "type": "string",
            "enum": [k.value for k in Kind],
            "description": "What the note itself indicates it came from.",
        },
        "title": {"type": "string", "description": "What this note is about."},
        "body": {"type": "string", "description": "The cleaned-up note, in markdown."},
    },
    "required": ["kind", "title", "body"],
    "additionalProperties": False,
}


# Opus 5 performs unusually well at low effort, and this is a cleanup task rather
# than a reasoning one — so low is the starting point, not a compromise.
type Effort = Literal["low", "medium", "high", "xhigh", "max"]


class Refused(RuntimeError):
    """Claude's safety classifiers declined the Capture."""


class ClaudeLanguageModel:
    def __init__(
        self,
        client: anthropic.Anthropic | None = None,
        effort: Effort = "low",
    ) -> None:
        self._client = client or anthropic.Anthropic()
        self._effort: Effort = effort

    @property
    def version(self) -> str:
        """Model, effort and prompt together — all three change the output."""
        prompt = sha256(f"{SYSTEM}{json.dumps(SCHEMA, sort_keys=True)}".encode()).hexdigest()[:8]
        return f"{MODEL}-{self._effort}-{prompt}"

    def enrich(self, capture: Document) -> Enrichment:
        response = self._client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM,
            output_config=OutputConfigParam(
                effort=self._effort,
                format={"type": "json_schema", "schema": SCHEMA},
            ),
            messages=[{"role": "user", "content": capture.body}],
        )
        # Check the stop reason before reading content: a refusal returns HTTP 200
        # with content empty or partial, so indexing straight into it would break.
        if response.stop_reason == "refusal":
            raise Refused(f"the capture was declined: {response.stop_details}")

        text = next(block.text for block in response.content if block.type == "text")
        parsed = json.loads(text)
        return Enrichment(
            kind=Kind(parsed["kind"]),
            title=parsed["title"],
            body=parsed["body"],
        )
