FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# The lock lives at the workspace root, so the build context is the repository
# root and only the pipeline member is installed.
COPY pyproject.toml uv.lock ./
COPY apps/pipeline/pyproject.toml apps/pipeline/
COPY apps/pipeline/src apps/pipeline/src

# --frozen resolves nothing: the committed lock decides, so builds are reproducible.
# --no-dev keeps ruff and mypy out of the runtime image.
RUN uv sync --frozen --no-dev --package pipeline

# Call the console script directly. `uv run` would re-sync on every start, pulling
# dev dependencies back in and doing network I/O at container startup — which a
# Cloud Run Job must never do (ADR-0013).
ENTRYPOINT ["/app/.venv/bin/pipeline"]
