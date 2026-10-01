---
name: t241-verify-that-third-party-libraries-use-secure-settings-and-t
description: Pin dependencies to reviewed versions and run a vulnerability audit on every build.
---

# T241: Verify that third party libraries use secure settings and the latest patches

**Category:** CODE_FIX
**SD Elements:** [T241](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T241/)
**Priority:** 10

**Finding:** Every dependency is declared with a caret range and no lower-bound security floor or audit step.

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
# pyproject.toml — exact pins reviewed on a schedule
fastapi = "0.115.6"
uvicorn = {extras = ["standard"], version = "0.34.0"}
sqlalchemy = "2.0.36"
python-jose = "3.3.0"
passlib = "1.7.4"
requests = "2.32.3"

# .github/workflows/ci.yml
      - run: pip-audit --strict --require-hashes -r requirements.txt
```

**Success Criteria:**
- Dependencies are pinned to exact versions in the lock file.
- An audit step fails the build on a known vulnerable version.
- Upgrades are reviewed rather than floating.

**Status:** Applied
