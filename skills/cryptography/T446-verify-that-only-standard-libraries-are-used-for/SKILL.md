---
name: t446-verify-that-only-standard-libraries-are-used-for-cryptograp
description: Generate all security-relevant values with the `secrets` module rather than `random`.
---

# T446: Verify that only standard libraries are used for cryptography

**Category:** CODE_FIX
**SD Elements:** [T446](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T446/)
**Priority:** 8

**Finding:** Referral codes are generated with the standard `random` module rather than a cryptographic library.

**Code to Fix:**
```python
# app/apis/referrals/utils.py lines 1-11
import random
import string

from db.models import User
from sqlalchemy.orm import Session


def _generate_code() -> str:
    """Generate an 8-character uppercase alphanumeric code."""
    characters = string.ascii_uppercase + string.digits
    return "".join(random.choice(characters) for _ in range(8))
```

**Required Fix:**
```python
# app/apis/referrals/utils.py
import secrets
import string

ALPHABET = string.ascii_uppercase + string.digits


def _generate_code(length: int = 12) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
```

**Success Criteria:**
- `import random` does not appear in any module that produces a token, code or identifier.
- All such values come from `secrets`.

**Status:** Applied
