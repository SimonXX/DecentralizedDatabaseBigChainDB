FROM mcr.microsoft.com/devcontainers/python:3.9

RUN apt-get update && apt-get install -y --no-install-recommends \
    jq \
    build-essential \
    libffi-dev \
    libssl-dev \
    libsodium-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
