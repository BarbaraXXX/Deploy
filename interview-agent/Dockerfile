FROM node:22-slim AS frontend
WORKDIR /build
COPY web/package.json web/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim
ARG PYPI_INDEX_URL=https://pypi.org/simple
ARG UV_VERSION=0.11.16
ENV PIP_INDEX_URL=${PYPI_INDEX_URL} \
    UV_INDEX_URL=${PYPI_INDEX_URL}
WORKDIR /app
RUN groupadd -r app && useradd -r -g app -d /app app
COPY pyproject.toml uv.lock ./
COPY src/ src/
RUN --mount=type=cache,target=/root/.cache/pip pip install "uv==${UV_VERSION}"
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-editable
COPY --from=frontend /build/dist ./web/dist/
RUN mkdir -p /app/data && chown app:app /app/data
USER app
ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/domains')" || exit 1

CMD ["uvicorn", "interview_agent.server:app", "--host", "0.0.0.0", "--port", "8000"]
