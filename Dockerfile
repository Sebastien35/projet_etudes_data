FROM python:3.12-alpine

WORKDIR /opt

# Copy requirements first (better Docker cache)
COPY requirements.txt .
COPY requirements-dev.txt .
COPY Makefile .

# Install build deps + make
RUN apk add --no-cache make gcc musl-dev && \
    make quickstart && \
    apk del gcc musl-dev  # Cleanup build deps

# Copy application source
COPY ./src .

