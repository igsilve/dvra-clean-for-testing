FROM python:3.10-slim-bookworm AS builder

RUN pip install poetry==1.4.2
WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes


FROM python:3.10-slim-bookworm AS runtime

LABEL org.opencontainers.image.description="dvra-clean-for-testing restaurant API"

RUN apt-get update \
    && apt-get -y install --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
WORKDIR /app

RUN useradd -m app \
    && chown app .
USER app
