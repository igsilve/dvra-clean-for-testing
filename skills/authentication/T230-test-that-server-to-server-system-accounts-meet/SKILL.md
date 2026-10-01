---
name: t230-test-that-server-to-server-system-accounts-meet-minimum-pas
description: Remove the hardcoded seed passwords and require machine and staff accounts to meet the password policy.
---

# T230: Test that server-to-server system accounts meet minimum password requirements

**Category:** CODE_FIX
**SD Elements:** [T230](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T230/)
**Priority:** 8

**Finding:** A seeded employee account uses the password "kaylee123", which meets no strength requirement.

**Code to Fix:**
```python
# app/init.py lines 30-38
    create_user_if_not_exists(
        db,
        username="Mike",
        password="kaylee123",
        first_name="Mike",
        last_name="",
        phone_number="(505) 146-0190",
        role=UserRole.EMPLOYEE,
    )
```

**Required Fix:**
```python
# app/init.py
def load_users(db: Session):
    for username, role, phone in SEED_ACCOUNTS:
        create_user_if_not_exists(
            db,
            username=username,
            password=generate_random_secret(),   # 32 chars from secrets.choice
            phone_number=phone,
            role=role,
            must_change_password=True,
        )
# generate_random_secret() already uses secrets.choice over letters+digits+punctuation.
```

**Success Criteria:**
- No literal password string remains in app/init.py.
- Seeded accounts are created with a high-entropy generated value.
- Seeded accounts are flagged to force a password change at first use.

**Status:** Applied
