FROM node:22-slim AS frontend
WORKDIR /build
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
RUN groupadd -r app && useradd -r -g app -d /app app
COPY pyproject.toml ./
COPY src/ src/
RUN pip install --no-cache-dir uv && uv pip install --system --no-cache -e .
COPY --from=frontend /build/dist ./web/dist/
RUN mkdir -p /app/data && chown app:app /app/data
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/domains')" || exit 1

CMD ["uvicorn", "interview_agent.server:app", "--host", "0.0.0.0", "--port", "8000"]
