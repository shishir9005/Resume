FROM python:3.11-slim

ENV FASTEMBED_CACHE_PATH=/app/.cache/fastembed \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
    libffi-dev fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

RUN python -m spacy download en_core_web_sm
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('sentence-transformers/all-MiniLM-L6-v2')"

COPY backend ./backend

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
