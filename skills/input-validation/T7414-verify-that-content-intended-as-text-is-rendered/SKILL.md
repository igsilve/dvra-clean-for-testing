---
name: t7414-verify-that-content-intended-as-text-is-rendered-safely-wi
description: Prove with a test that stored text is returned as data and never interpreted as markup.
---

# T7414: Verify that content intended as text is rendered safely without XSS injection risk

**Category:** CODE_FIX
**SD Elements:** [T7414](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7414/)
**Priority:** 7

**Finding:** Stored text fields are returned verbatim through the API with no encoding guarantee for HTML consumers.

**Code to Fix:**
```python
# app/apis/menu/services/create_menu_item_service.py lines 15-22
def create_menu_item(
    menu_item: schemas.MenuItemCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    auth=Depends(RolesBasedAuthChecker([UserRole.EMPLOYEE, UserRole.CHEF])),
):
    db_item = utils.create_menu_item(db, menu_item)
    return db_item
```

**Required Fix:**
```python
# app/tests/security/test_text_rendering.py
PAYLOAD = "<script>alert(1)</script>"


@pytest.mark.security
def test_menu_text_is_returned_as_data(client, chef_token):
    client.put(
        "/menu",
        headers={"Authorization": f"Bearer {chef_token}"},
        json={"name": PAYLOAD, "price": 1.0, "category": "Test"},
    )
    response = client.get("/menu")
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.json()[-1]["name"] == PAYLOAD      # stored verbatim, not executed
```

**Success Criteria:**
- A test round-trips a script payload and asserts the response is JSON with nosniff.
- No endpoint returns stored text inside an HTML document.

**Status:** Applied
