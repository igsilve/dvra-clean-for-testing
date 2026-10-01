---
name: t323-test-that-default-accounts-are-disabled-or-default-password
description: Ensure no account ships with a known password and prove it with a test.
---

# T323: Test that default accounts are disabled or default passwords are changed

**Category:** CODE_FIX
**SD Elements:** [T323](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T323/)
**Priority:** 9

**Finding:** Five accounts are seeded with hardcoded, weak passwords that are never forced to change.

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
# app/tests/security/test_default_accounts.py
KNOWN_DEFAULTS = ["kaylee123", "Th4tsMyP4ssw0rd!", "12345678", "password123", "password456"]


@pytest.mark.security
@pytest.mark.parametrize("username,password", [("Mike", "kaylee123"), ("hhm", "12345678")])
def test_seeded_defaults_do_not_authenticate(client, username, password):
    response = client.post("/token", data={"username": username, "password": password})
    assert response.status_code == 401
```

**Success Criteria:**
- A test asserts that each historically seeded credential fails authentication.
- Grepping the repository for the known default passwords returns nothing.

**Status:** Applied
