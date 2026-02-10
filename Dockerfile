# OpenLineage YAML Tool
# Multi-stage build for a minimal production image

# ── Build stage ──────────────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
COPY schemas/ schemas/

RUN pip install --no-cache-dir --prefix=/install .

# ── Runtime stage ────────────────────────────────────────────
FROM python:3.13-slim

LABEL maintainer="Data Engineering"
LABEL description="OpenLineage YAML Tool — validate and publish lineage events from YAML definitions"

# Copy only the installed packages from the builder
COPY --from=builder /install /usr/local
COPY --from=builder /app/src /app/src
COPY --from=builder /app/schemas /app/schemas

WORKDIR /workspace

# In GitLab CI, the repo is cloned into the working directory,
# so the user's lineage/ folder will be at ./lineage by default.
ENTRYPOINT ["python", "-m", "src.main"]
CMD ["--help"]
