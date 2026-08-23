"""The enrichment contract, shared by every provider adapter.

Prompt and schema live here rather than in one provider's module because they are
what the pipeline asks for, not how a particular vendor is asked. Two adapters
sharing them is what makes their outputs comparable — and what makes the pipeline
version meaningful across a provider switch.
"""

import json
from hashlib import sha256
from typing import Any

from pipeline.domain.kind import Kind
from pipeline.domain.language import Enrichment

SYSTEM = """You clean up dictated notes for a personal knowledge base.

The text you receive was spoken aloud and transcribed, so it rambles, repeats
itself, and contains false starts. Turn it into something the author will want to
reread in a year.

Rules, in order of importance:

1. Never add anything the author did not say. No invented facts, sources, names,
   figures or conclusions — and no invented *connections*. If they said two things
   one after another, leave them one after another. Words like "because of this",
   "therefore" and "as a result" assert reasoning the author did not do, and are
   harder to catch than a wrong fact because nothing looks out of place.

2. Apply the author's own corrections. Dictated notes contain self-corrections:
   "no wait", "actually", "correction: X not Y". The corrected version is what the
   author meant — write that, and drop both the mistake and the correction itself.
   Never keep a correction whose subject you removed: a note reading "Correction:
   October, not November" with no November left in it is worse than either version.

3. Match the author's certainty exactly. If they said something flatly, say it
   flatly — never soften it with "seems", "suggests", "appears" or "may". If they
   hedged, keep the hedge. Adding caution they did not express misrepresents them
   just as much as removing caution they did.

4. Be shorter than what you were given, or about the same length. You are removing
   noise, not restating. If your version is longer, you have padded it. Filler is
   noise; specifics are not — keep the concrete details of where, when and who,
   because those are what make a note recallable later.

5. Keep the author's voice and vocabulary. Their casual word is usually the honest
   one: "the cold shower thing" says they have not pinned it down yet, and "routine"
   would claim more than they know. Do not translate into business register.

6. Give it structure only where the content already has it. Do not impose headings
   or bullet lists on a single continuous thought.

7. Write a title that says what this note is actually about — not a category, and
   not the first sentence restated.

Choose the `kind` from what the note itself says, not from any metadata:
  podcast  — a takeaway from something the author listened to
  article  — a takeaway from something the author read
  meeting  — notes from a conversation the author took part in
  thought  — the author's own thinking, not prompted by a specific source

Judge `kind` on the content alone. Getting this wrong in either direction is
worse than useless: it is how the system detects that provenance went missing.

Reply with JSON only: an object with the keys `kind`, `title` and `body`."""

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

CONTRACT = sha256(f"{SYSTEM}{json.dumps(SCHEMA, sort_keys=True)}".encode()).hexdigest()[:8]


class Malformed(RuntimeError):
    """The model did not honour the schema.

    Raised rather than repaired. Schema adherence varies widely between models —
    small local ones are notably worse at it — and silently patching a bad reply
    would put invented or truncated content into the Vault under the author's name.
    """


def parse(text: str) -> Enrichment:
    """Turn a model's reply into an Enrichment, or fail loudly."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as broken:
        raise Malformed(f"reply was not JSON: {text[:200]}") from broken

    if not isinstance(payload, dict):
        raise Malformed(f"reply was not a JSON object: {text[:200]}")

    missing = {"kind", "title", "body"} - payload.keys()
    if missing:
        raise Malformed(f"reply is missing {sorted(missing)}: {text[:200]}")

    try:
        kind = Kind(payload["kind"])
    except ValueError as unknown:
        raise Malformed(f"'{payload['kind']}' is not one of {[k.value for k in Kind]}") from unknown

    return Enrichment(kind=kind, title=str(payload["title"]), body=str(payload["body"]))
