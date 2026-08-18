FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY tests ./tests
COPY config ./config
COPY scripts ./scripts
COPY docs ./docs
COPY assets ./assets

RUN pip install --no-cache-dir -e ".[test]"

CMD ["sh", "-c", "ruff check src tests && mypy && pytest -q"]
