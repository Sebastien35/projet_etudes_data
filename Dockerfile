FROM python:3.12

WORKDIR /opt

# Copy requirements first (meilleur cache Docker)
COPY requirements.txt .
COPY requirements-dev.txt .
COPY Makefile .

# Install dependencies
RUN apk add make 
RUN make quickstart

# Copy application source
COPY ./src .
