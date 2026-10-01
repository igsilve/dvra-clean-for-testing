---
name: t587-verify-that-cryptographically-secure-algorithms-are-used-fo
description: Draw referral codes from a cryptographically secure source and give them enough entropy to resist guessing.
---

# T587: Verify that cryptographically secure algorithms are used for random number generation

**Category:** CODE_FIX
**SD Elements:** [T587](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T587/)
**Priority:** 7

**Finding:** random.choice draws from a predictable Mersenne Twister stream, so referral codes are guessable.

**Code to Fix:**
```python
# app/apis/referrals/utils.py lines 8-11
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
CODE_LENGTH = 12        # ~62 bits of entropy


def _generate_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
```

**Success Criteria:**
- The generator uses `secrets`, not `random`.
- Code length provides at least 64 bits of entropy.
- Collisions are handled by the database unique constraint with a retry.

**Status:** Applied
