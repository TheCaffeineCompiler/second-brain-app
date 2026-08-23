"""What a freshly provisioned Vault contains.

Only **decided** artifacts are seeded (ADR-0011). The derived regions — notes and
topics — are not created here; they appear when the pipeline first writes them.
Seeding pipeline-owned regions would blur exactly the ownership the split exists
to establish.
"""

from pipeline.domain.document import Document

REGISTRY = Document(
    type="registry",
    body="""# Registry

The canonical name for every entity you want a Topic page for, and the aliases that
should resolve to it. This file is yours — the pipeline reads it and never writes to
it (ADR-0005).

Entities the pipeline has noticed but you have not admitted yet are listed in
`candidates.md`. Promote one by moving it here and giving it its canonical name.

## People

## Organizations

## Concepts
""",
)

README = Document(
    type="readme",
    body="""# Vault

Notes for a Second Brain, in Open Knowledge Format. Plain markdown with YAML
frontmatter — readable by `cat`, by Obsidian, and by any agent.

- `captures/` — what you recorded, exactly as you recorded it. Yours to write and
  edit; the system never modifies a Capture.
- `registry.md` — the entities you have named. Yours.
- `notes/`, `topics/` — derived by the pipeline. **Do not edit these by hand**: they
  are rebuilt from your Captures, and an edit will be detected and refused rather
  than silently overwritten.
- `log.md` — what each pipeline run did.
""",
)

# OKF reserves log.md for chronological history and exempts it from the frontmatter
# rule, so it is plain text rather than a Document.
LOG = """# Log

What each pipeline run did.
"""

DECIDED: dict[str, Document] = {"registry": REGISTRY, "readme": README}
