FROM python:3.12-slim

WORKDIR /app
RUN groupadd -r app && useradd -r -g app -d /app app

COPY pyproject.toml ./
COPY src/ src/
RUN pip install --no-cache-dir uv && uv pip install --system --no-cache -e .

RUN mkdir -p /app/data && chown app:app /app/data
USER app

EXPOSE 9000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9000/api/profiles')" || exit 1

CMD ["python", "-m", "interview_vectordb"]
