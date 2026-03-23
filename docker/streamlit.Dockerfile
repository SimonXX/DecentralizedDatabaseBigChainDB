FROM python:3.6-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    libsodium-dev \
    python3-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV SODIUM_INSTALL=system

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "src/DecentralizedDatabaseDEMO.py", \
    "--server.address=0.0.0.0", \
    "--server.port=8501", \
    "--server.headless=true", \
    "--browser.gatherUsageStats=false"]
