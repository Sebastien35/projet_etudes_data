FROM python:3.12-alpine AS builder

RUN apk add --no-cache \
    build-base=0.5-r3 \
    libffi-dev=3.4.6-r0 \
    openssl-dev=3.3.2-r1 \
    python3-dev=3.12.9-r0 \
    rust=1.84.0-r0

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /opt

COPY pyproject.toml uv.lock ./
COPY src ./src

# Installer les dépendances dans le stage builder
RUN uv sync --frozen --no-dev

FROM python:3.12-alpine AS runtime

# Copier uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copier l'environnement virtuel et le code depuis le builder
COPY --from=builder /opt /opt

WORKDIR /opt
