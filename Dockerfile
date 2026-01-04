FROM python:3.12.2-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

ENV PATH="/app/.venv/bin:$PATH"

COPY src ./src
COPY agent.py ./
COPY coding-standards ./coding-standards
COPY profiles ./profiles
COPY docs ./docs

CMD ["python", "agent.py"]
