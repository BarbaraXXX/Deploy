FROM node:23-slim AS frontend
WORKDIR /build
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src/ src/
RUN pip install --no-cache-dir uv && uv pip install --system --no-cache -e .
COPY --from=frontend /build/dist ./web/dist/
RUN mkdir -p /app/data

EXPOSE 8000
CMD ["uvicorn", "interview_agent.server:app", "--host", "0.0.0.0", "--port", "8000"]
