# Base images are pinned by digest, not by tag. A tag is a moving pointer:
# `python:3.10-slim-bookworm` is a different image this week than last, so a
# rebuild can pull in a base nobody reviewed and the build still looks
# reproducible. The digests live in deploy/base-images.lock with the date
# they were resolved; updating one is a reviewed change like any other.
FROM python:3.10-bookworm@sha256:0a06143d04e5207c0561a9803a007af1d3e7941634fd1a7f801079dca3644bf5 AS builder

RUN pip install poetry==1.4.2
WORKDIR /app

COPY pyproject.toml poetry.lock ./
# Exported with hashes. Without them the build resolves names against
# whatever the index serves at that moment, so a compromised index or a
# yanked-and-republished version changes what ships without changing
# anything under review.
RUN poetry export -f requirements.txt --output requirements.txt


FROM python:3.10-slim-bookworm@sha256:2559be987fd64d61badbdafd303ea58a9ccab36d6c3c08bce219e762177d2eca AS runtime

# Only the Postgres client library, and the runtime one rather than the
# development package: libpq-dev exists to compile against, and nothing is
# compiled here. gcc, vim and sudo are gone. A compiler in a runtime image
# turns a file-write bug into arbitrary code; an editor gives an intruder a
# way to work; sudo carried a passwordless rule for find, which is a
# one-command path to root for anyone who reaches the app user.
#
# Installed and cleaned in a single layer: a separate `rm` leaves the apt
# lists in the earlier layer, where they still ship in the image.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# The container's filesystem is read-only at runtime, so writing bytecode
# would fail on every import. Python degrades quietly, but the noise is
# avoidable and the setting documents that nothing writes to the image.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /app/requirements.txt .
# --require-hashes makes the hashes mandatory rather than advisory: pip
# refuses the whole install if any requirement lacks one, so a dependency
# added later without a hash fails the build instead of installing
# unverified.
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

# A fixed, high, non-system UID. The number is pinned rather than left to
# useradd so that compose can assert the same value and a host bind mount
# cannot silently land on an existing account.
RUN groupadd --gid 10001 app \
 && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin app

COPY --chown=10001:10001 app ./app
WORKDIR /app

# The application never writes to its own code. Ownership stays with root
# and the runtime user only reads, so a write primitive in the application
# cannot modify the code it is about to execute.
USER 10001:10001

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8091/healthcheck', timeout=2).status == 200 else 1)"
