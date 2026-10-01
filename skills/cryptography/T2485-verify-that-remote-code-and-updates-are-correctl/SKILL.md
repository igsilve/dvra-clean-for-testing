---
name: t2485-verify-that-remote-code-and-updates-are-correctly-encrypte
description: Verify package integrity at install time by requiring hashes for every dependency.
---

# T2485: Verify that remote code and updates are correctly encrypted and signed (server side)

**Category:** CODE_FIX
**SD Elements:** [T2485](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2485/)
**Priority:** 9

**Finding:** Dependencies are declared with caret ranges and no hashes, so the integrity of fetched packages is never verified.

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
# generated and committed alongside pyproject.toml
poetry export --format requirements.txt --output requirements.txt   # with hashes

# Dockerfile
RUN pip install --no-cache-dir --require-hashes -r requirements.txt
```

**Success Criteria:**
- The exported requirements file contains a hash for every package.
- `--require-hashes` is passed to pip so a mismatch aborts the build.
- The lock file is committed and changes are reviewed.

**Status:** Applied
