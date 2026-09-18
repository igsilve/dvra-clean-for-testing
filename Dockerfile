FROM python:3.10-bookworm as builder

RUN pip install poetry==1.4.2
WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes


FROM python:3.10-slim-bookworm as runtime

RUN apt-get update \
	&& apt-get -y install --no-install-recommends libpq-dev gcc \
	&& rm -rf /var/lib/apt/lists/*

RUN useradd -m app

COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app app ./app
WORKDIR /app

USER app
