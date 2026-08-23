"""LanguageModel over any OpenAI-compatible endpoint.

One adapter covers a lot of ground: Ollama and LM Studio locally, and OpenRouter,
Together, vLLM and OpenAI itself remotely. Local endpoints matter for the same
reason local transcription does (ADR-0017) — otherwise every Capture is sent to a
third party on its way into the Vault.

Schema adherence is much weaker here than on a frontier model: many endpoints
accept `response_format` and then ignore it. That is why `parse` validates rather
than trusts, and why a run against a small local model will surface `Malformed`
where a larger one does not.
"""

from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from openai.types.shared_params import ResponseFormatJSONSchema
from openai.types.shared_params.response_format_json_schema import JSONSchema

from pipeline.adapters.enrichment_schema import CONTRACT, SCHEMA, SYSTEM, Malformed, parse
from pipeline.domain.document import Document
from pipeline.domain.language import Enrichment

RESPONSE_FORMAT = ResponseFormatJSONSchema(
    type="json_schema",
    json_schema=JSONSchema(name="enrichment", schema=SCHEMA, strict=True),
)


class OpenAICompatibleLanguageModel:
    def __init__(
        self,
        model: str,
        base_url: str | None = None,
        client: OpenAI | None = None,
    ) -> None:
        self._client = client or OpenAI(base_url=base_url)
        self._model = model
        # Part of the version: the same model served by two endpoints can behave
        # differently, and a local endpoint is not the hosted one.
        self._endpoint = base_url or "openai"

    @property
    def version(self) -> str:
        return f"openai-{self._endpoint}-{self._model}-{CONTRACT}"

    def enrich(self, capture: Document) -> Enrichment:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                ChatCompletionSystemMessageParam(role="system", content=SYSTEM),
                ChatCompletionUserMessageParam(role="user", content=capture.body),
            ],
            response_format=RESPONSE_FORMAT,
        )
        text = response.choices[0].message.content
        if text is None:
            raise Malformed("the endpoint returned no content")
        return parse(text)
