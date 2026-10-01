---
name: t296-test-that-unencrypted-confidential-data-is-not-stored-witho
description: Encrypt or hash the sensitive columns and confirm with a test that they are unreadable at rest.
---

# T296: Test that unencrypted confidential data is not stored without access control mechanisms

**Category:** CODE_FIX
**SD Elements:** [T296](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T296/)
**Priority:** 7

**Finding:** reset_password_code and phone_number are stored as plain columns with no encryption and no column-level access control.

**Code to Fix:**
```python
# app/db/models.py lines 33-45
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER)
    first_name = Column(String)
    last_name = Column(String)
    phone_number = Column(String, unique=True, index=True)
    reset_password_code = Column(String, nullable=True)
    reset_password_code_expiry_date = Column(DateTime, nullable=True)
    referral_code = Column(String, unique=True, index=True, nullable=True)
```

**Required Fix:**
```python
# app/db/models.py
class User(Base):
    __tablename__ = "users"

    password = Column(String, nullable=False)                    # bcrypt/argon2 hash
    reset_password_code_hash = Column(String, nullable=True)     # hashed, not plaintext
    phone_number = Column(EncryptedType(String, settings.COLUMN_ENCRYPTION_KEY), unique=True, index=True)

# and the reset flow stores/compares only the hash:
#   user.reset_password_code_hash = pwd_context.hash(code)
```

**Success Criteria:**
- The reset code is stored hashed, never in plaintext.
- Personally identifying columns are encrypted at rest with a key held outside the database.
- Reading the table directly reveals no usable secret.

**Status:** Applied
