---
name: t7374-pin-hash-and-continuously-audit-python-dependencies-fastap
description: Pin, hash and continuously audit the Python dependency set.
---

# T7374: Pin, hash, and continuously audit Python dependencies (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7374](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7374/)
**Priority:** 10

**Finding:** Dependencies are unpinned caret ranges with no hash verification and no scheduled audit.

**Code to Fix:**
```toml
# pyproject.toml lines 9-31
[tool.poetry.dependencies]
python = "^3.10"
fastapi = "^0.103.0"
uvicorn = {extras = ["standard"], version = "^0.23.2"}
httpx = "^0.24.1"
sqlalchemy = "^2.0.20"
psycopg2 = "^2.9.7"
python-jose = "^3.3.0"
passlib = "^1.7.4"
python-multipart = "^0.0.9"
bcrypt = "^4.1.2"
requests = "^2.31.0"
alembic = "^1.13.1"
pytest = "8.3.4"
pytest-mock = "^3.14.0"
requests-mock = "^1.11.0"
colorama = "^0.4.6"
pylint = "^3.2.5"
pytest-json-report = "^1.5.0"
pytest-asyncio = "^0.25.0"
pillow = "^11.1.0"
psutil = "^7.0.0"
slowapi = "^0.1.9"
```

**Required Fix:**
```toml
# Dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

# .github/workflows/ci.yml
      - run: poetry lock --check
      - run: poetry export -f requirements.txt --output requirements.txt   # with hashes
      - run: pip-audit -r requirements.txt --strict
```

**Success Criteria:**
- The lock file is committed and CI fails if it is stale.
- Installation requires hashes.
- A scheduled job re-runs the audit against the pinned set.

**Status:** Applied
