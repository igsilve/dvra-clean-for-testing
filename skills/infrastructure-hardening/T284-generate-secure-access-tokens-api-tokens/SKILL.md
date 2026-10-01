---
name: t284-generate-secure-access-tokens-api-tokens
description: Generate token-signing material from a cryptographic source, or require it from configuration, never from `random`.
---

# T284: Generate secure access tokens (API tokens)

**Category:** CODE_FIX
**SD Elements:** [T284](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T284/)
**Priority:** 7

**Finding:** The fallback signing secret is six decimal digits drawn from the non-cryptographic `random` module.

**Code to Fix:**
```python
# app/config.py lines 22-27
def generate_random_secret():
    return "".join(random.choices("1234567890", k=6))


class Settings:
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", generate_random_secret())
```

**Required Fix:**
```python
# app/config.py
# generate_random_secret() is deleted; the key must be supplied:
JWT_SECRET_KEY: str = _required("JWT_SECRET_KEY")

# If a value must ever be generated operationally, it is done out of band:
#   python -c "import secrets; print(secrets.token_urlsafe(48))"
```

**Success Criteria:**
- `random` is not used for any token or key.
- Generated tokens carry at least 256 bits of entropy.
- The application never invents a signing key at runtime.

**Status:** Applied
