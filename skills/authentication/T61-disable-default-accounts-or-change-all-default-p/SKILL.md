---
name: t61-disable-default-accounts-or-change-all-default-passwords
description: Stop seeding fixed passwords; generate them and require a change at first login.
---

# T61: Disable default accounts or change all default passwords

**Category:** CODE_FIX
**SD Elements:** [T61](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T61/)
**Priority:** 9

**Finding:** Default accounts for Mike, Saul, hhm, johndoe and alicesmith are created with fixed passwords and left enabled.

**Code to Fix:**
```python
# app/init.py lines 30-73
    create_user_if_not_exists(
        db,
        username="Mike",
        password="kaylee123",
        first_name="Mike",
        last_name="",
        phone_number="(505) 146-0190",
        role=UserRole.EMPLOYEE,
    )
    create_user_if_not_exists(
        db,
        username="Saul",
        password="Th4tsMyP4ssw0rd!",
        first_name="Saul",
        last_name="",
        phone_number="(505) 842-5662",
        role=UserRole.EMPLOYEE,
    )
    create_user_if_not_exists(
        db,
        username="hhm",
        password="12345678",
        first_name="Howard",
        last_name="Hamlin",
        phone_number="(505) 56434-7345",
        role=UserRole.CUSTOMER,
    )
    create_user_if_not_exists(
        db,
        username="johndoe",
        password="password123",
        first_name="John",
        last_name="Doe",
        phone_number="(505) 56434-7346",
        role=UserRole.CUSTOMER,
    )
    create_user_if_not_exists(
        db,
        username="alicesmith",
        password="password456",
        first_name="Alice",
        last_name="Smith",
        phone_number="(505) 53436-7347",
        role=UserRole.CUSTOMER,
```

**Required Fix:**
```python
# app/init.py
create_user_if_not_exists(
    db,
    username="Mike",
    password=generate_random_secret(),
    first_name="Mike",
    last_name="",
    phone_number="(505) 146-0190",
    role=UserRole.EMPLOYEE,
)
# ...and identically for every other seeded account; print nothing to stdout.
```

**Success Criteria:**
- No hardcoded password literal remains in the seeding code.
- Generated credentials are delivered out of band, not logged.
- Accounts that are not required for operation are not created at all.

**Status:** Applied
