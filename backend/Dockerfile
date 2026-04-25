FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    ffmpeg \
    espeak-ng \
    libsndfile1 \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Trust the host CA bundle (handles intercepting TLS proxies)
COPY ca-certificates.crt /usr/local/share/ca-certificates/custom.crt
RUN update-ca-certificates

RUN python3.11 -m pip install --upgrade pip \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host pypi.python.org

WORKDIR /app

COPY requirements.txt .
RUN python3.11 -m pip install --no-cache-dir -r requirements.txt \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host pypi.python.org

COPY . .

ENV PYTHONPATH=/app
ENV PYTHON=python3.11
