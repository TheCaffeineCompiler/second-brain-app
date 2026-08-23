"""Both adapters, driven against a fake endpoint.

This verifies the request is accepted and the reply is turned into an Enrichment.
It does **not** verify that the real vendors accept these request shapes — only a
live call does that.
"""

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest

from pipeline.adapters.enrichment_schema import Malformed, parse
from pipeline.adapters.language import UnknownProvider, from_environment
from pipeline.adapters.stub_language import StubLanguageModel
from pipeline.domain.document import Document
from pipeline.domain.kind import Kind

ENRICHED = json.dumps({"kind": "podcast", "title": "Sleep latency", "body": "Cleaned up."})
CAPTURE = Document(type="capture", body="um so the thing about sleep latency is")

RECEIVED: list[dict[str, Any]] = []


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        body = self.rfile.read(int(self.headers["Content-Length"]))
        RECEIVED.append(json.loads(body))
        reply: dict[str, Any]
        if "/chat/completions" in self.path:
            reply = {"choices": [{"message": {"role": "assistant", "content": ENRICHED}}]}
        else:
            reply = {
                "id": "msg_1",
                "type": "message",
                "role": "assistant",
                "model": "fake",
                "content": [{"type": "text", "text": ENRICHED}],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
        payload = json.dumps(reply).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args: Any) -> None:
        pass


@pytest.fixture
def endpoint() -> Iterator[str]:
    RECEIVED.clear()
    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def test_an_openai_compatible_endpoint_produces_an_enrichment(endpoint: str) -> None:
    from openai import OpenAI

    from pipeline.adapters.openai_compatible import OpenAICompatibleLanguageModel

    model = OpenAICompatibleLanguageModel(
        model="llama3.1",
        base_url=f"{endpoint}/v1",
        client=OpenAI(base_url=f"{endpoint}/v1", api_key="unused"),
    )
    enrichment = model.enrich(CAPTURE)

    assert enrichment.kind is Kind.PODCAST
    assert enrichment.title == "Sleep latency"
    assert RECEIVED[0]["response_format"]["type"] == "json_schema"


def test_claude_produces_an_enrichment(endpoint: str) -> None:
    import anthropic

    from pipeline.adapters.claude import ClaudeLanguageModel

    model = ClaudeLanguageModel(client=anthropic.Anthropic(base_url=endpoint, api_key="unused"))
    enrichment = model.enrich(CAPTURE)

    assert enrichment.kind is Kind.PODCAST
    assert RECEIVED[0]["output_config"]["format"]["type"] == "json_schema"
    assert "temperature" not in RECEIVED[0], "Opus 5 rejects sampling parameters"


def test_both_providers_ask_for_the_same_thing(endpoint: str) -> None:
    """A shared prompt and schema are what make a provider switch comparable."""
    import anthropic
    from openai import OpenAI

    from pipeline.adapters.claude import ClaudeLanguageModel
    from pipeline.adapters.openai_compatible import OpenAICompatibleLanguageModel

    ClaudeLanguageModel(client=anthropic.Anthropic(base_url=endpoint, api_key="x")).enrich(CAPTURE)
    OpenAICompatibleLanguageModel(
        model="m", client=OpenAI(base_url=f"{endpoint}/v1", api_key="x")
    ).enrich(CAPTURE)

    anthropic_schema = RECEIVED[0]["output_config"]["format"]["schema"]
    openai_schema = RECEIVED[1]["response_format"]["json_schema"]["schema"]
    assert anthropic_schema == openai_schema


def test_switching_provider_marks_the_corpus_stale(endpoint: str) -> None:
    """Two providers are not interchangeable outputs — a switch must re-derive."""
    import anthropic
    from openai import OpenAI

    from pipeline.adapters.claude import ClaudeLanguageModel
    from pipeline.adapters.openai_compatible import OpenAICompatibleLanguageModel

    claude = ClaudeLanguageModel(client=anthropic.Anthropic(base_url=endpoint, api_key="x"))
    local = OpenAICompatibleLanguageModel(
        model="llama3.1",
        base_url="http://localhost:11434/v1",
        client=OpenAI(base_url=f"{endpoint}/v1", api_key="x"),
    )
    assert claude.version != local.version


def test_a_reply_that_ignores_the_schema_fails_loudly() -> None:
    """Small local models often ignore response_format; repairing the reply
    silently would put invented content into the Vault."""
    with pytest.raises(Malformed, match="not JSON"):
        parse("Sure! Here's your note:")
    with pytest.raises(Malformed, match="missing"):
        parse(json.dumps({"kind": "podcast", "title": "no body"}))
    with pytest.raises(Malformed, match="not one of"):
        parse(json.dumps({"kind": "tweet", "title": "t", "body": "b"}))


def test_the_stub_needs_no_credentials_or_network() -> None:
    assert isinstance(from_environment("stub"), StubLanguageModel)


def test_an_unknown_provider_says_what_is_available() -> None:
    with pytest.raises(UnknownProvider, match="anthropic"):
        from_environment("gpt5-please")


def test_the_openai_provider_insists_on_a_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """There is no sensible default across OpenAI, OpenRouter and Ollama."""
    monkeypatch.delenv("LLM_MODEL", raising=False)
    with pytest.raises(UnknownProvider, match="LLM_MODEL"):
        from_environment("openai")
