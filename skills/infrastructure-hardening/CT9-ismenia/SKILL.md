---
name: ct9-ismenia
description: Make the deployment environment an explicit, validated choice rather than a silent default.
---

# CT9: Ismenia

**Category:** CODE_FIX
**SD Elements:** [CT9](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-CT9/)
**Priority:** 10

**Finding:** The environment selector defaults to PRODUCTION while every other default in this module is a development convenience, so the deployed configuration is not deliberately chosen.

**Code to Fix:**
```python
# app/config.py lines 13-19
class ENV(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


ENVIRONMENT = ENV(os.getenv("ENV", ENV.PRODUCTION.value))
```

**Required Fix:**
```python
# app/config.py
_raw_env = os.getenv("ENV")
if _raw_env is None:
    raise RuntimeError("ENV must be set explicitly to development, testing or production")

ENVIRONMENT = ENV(_raw_env)
```

**Success Criteria:**
- The process refuses to start when ENV is unset.
- Each environment supplies its own configuration values rather than falling back to a default.

**Status:** Applied
