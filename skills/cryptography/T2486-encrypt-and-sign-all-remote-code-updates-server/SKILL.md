---
name: t2486-encrypt-and-sign-all-remote-code-updates-server-side
description: Sign the artifacts this service produces and verify signatures on what it consumes.
---

# T2486: Encrypt and sign all remote code/updates (server side)

**Category:** CODE_FIX
**SD Elements:** [T2486](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2486/)
**Priority:** 9

**Finding:** There is no signing or integrity metadata for the code the service pulls in at build time.

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
# .github/workflows/release.yml
      - name: Sign image
        run: |
          cosign sign --yes "ghcr.io/${{ github.repository }}@${DIGEST}"

# deploy step
      - name: Verify before deploy
        run: |
          cosign verify --certificate-identity-regexp '.*' \
            --certificate-oidc-issuer https://token.actions.githubusercontent.com \
            "ghcr.io/${{ github.repository }}@${DIGEST}"
```

**Success Criteria:**
- Every released artifact carries a verifiable signature.
- Deployment fails when the signature cannot be verified.
- Signing keys are managed outside the repository.

**Status:** Applied
