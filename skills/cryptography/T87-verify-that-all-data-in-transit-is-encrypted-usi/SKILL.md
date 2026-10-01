---
name: t87-verify-that-all-data-in-transit-is-encrypted-using-a-secure
description: Require TLS on the database connection and verify the server certificate.
---

# T87: Verify that all data in transit is encrypted using a secure TLS channel

**Category:** CODE_FIX
**SD Elements:** [T87](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T87/)
**Priority:** 8

**Finding:** The PostgreSQL engine is created from a URL with no sslmode, so the database connection can run in plaintext.

**Code to Fix:**
```python
# app/db/session.py lines 21-22
    else:
        engine = create_engine(sqlalchemy_database_url)
```

**Required Fix:**
```python
# app/config.py
    @property
    def DATABASE_URL(self) -> str:
        if self.DB_BACKEND == "memory":
            return "sqlite://"
        return (
            f"postgresql://{quote_plus(self.POSTGRES_USER)}:{quote_plus(self.POSTGRES_PASSWORD)}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            f"?sslmode=verify-full&sslrootcert={self.POSTGRES_CA_PATH}"
        )
```

**Success Criteria:**
- The connection string requires `sslmode=verify-full`.
- A CA certificate path is configured and the server certificate is validated.
- A plaintext connection attempt is refused by the server.

**Status:** Applied
