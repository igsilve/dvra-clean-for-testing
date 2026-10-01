---
name: t2599-protect-against-connection-string-parameter-pollution
description: Build the connection string from properly escaped components, or pass them as separate parameters.
---

# T2599: Protect against connection string parameter pollution

**Category:** CODE_FIX
**SD Elements:** [T2599](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2599/)
**Priority:** 9

**Finding:** The database URL is assembled by string interpolation of five environment values with no escaping, so a value containing a delimiter can inject connection parameters.

**Code to Fix:**
```python
# app/config.py lines 49-53
    @property
    def DATABASE_URL(self) -> str:
        if self.DB_BACKEND == "memory":
            return "sqlite://"
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
```

**Required Fix:**
```python
# app/config.py
from sqlalchemy.engine import URL

    @property
    def DATABASE_URL(self) -> URL | str:
        if self.DB_BACKEND == "memory":
            return "sqlite://"
        return URL.create(
            "postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=int(self.POSTGRES_PORT),
            database=self.POSTGRES_DB,
            query={"sslmode": "verify-full"},
        )
```

**Success Criteria:**
- The connection URL is constructed through a library that escapes each component.
- A password containing `@`, `/` or `?` does not change the parsed host or database.
- Connection options are supplied as structured query parameters.

**Status:** Applied
