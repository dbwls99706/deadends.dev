# MCP server over stdio.
#
# The canon corpus is data, not a runtime dependency: ~2,400 JSON files are
# copied into the image so the server answers without network access. That is
# also what makes the image reproducible - a lookup returns the same answer for
# a given tag forever.
FROM python:3.12-slim

WORKDIR /app

# Install dependencies before copying the corpus so that adding canons - which
# happens twice a day - does not invalidate the dependency layer.
COPY pyproject.toml README.md ./
COPY generator/ ./generator/
COPY mcp/ ./mcp/
RUN pip install --no-cache-dir -e ".[mcp]"

COPY data/canons/ ./data/canons/
COPY data/outcomes/ ./data/outcomes/

# Read-only workload; nothing here needs root.
RUN useradd --create-home --uid 1000 mcp && chown -R mcp:mcp /app
USER mcp

ENV PYTHONUNBUFFERED=1

# Optional tuning, documented in README:
#   DEADENDS_PREFERRED_DOMAINS  comma-separated domains to rank first
#   DEADENDS_MAX_RESULTS        1-20, default 10
#   DEADENDS_VERBOSE            "false" to trim workaround detail

# stdio transport: the client speaks JSON-RPC over stdin/stdout, so there is no
# port to expose and no healthcheck to run - readiness is the first response.
ENTRYPOINT ["python", "-m", "mcp.server"]
