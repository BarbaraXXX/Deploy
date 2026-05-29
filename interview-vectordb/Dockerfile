FROM python:3.12-slim
ARG PYPI_INDEX_URL=https://pypi.org/simple
ARG UV_VERSION=0.11.16
ARG APP_UID=10001
ARG APP_GID=10001
ENV PIP_INDEX_URL=${PYPI_INDEX_URL} \
    UV_INDEX_URL=${PYPI_INDEX_URL}

WORKDIR /app
RUN groupadd -g "${APP_GID}" app && useradd -u "${APP_UID}" -g app -d /app -M -s /usr/sbin/nologin app

COPY pyproject.toml uv.lock ./
COPY src/ src/
RUN --mount=type=cache,target=/root/.cache/pip pip install "uv==${UV_VERSION}"
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-editable

RUN mkdir -p /app/data && chown app:app /app/data
USER app
ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 9000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9000/healthz')" || exit 1

CMD ["python", "-m", "interview_vectordb"]
