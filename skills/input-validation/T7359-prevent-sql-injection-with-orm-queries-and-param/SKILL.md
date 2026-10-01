---
name: t7359-prevent-sql-injection-with-orm-queries-and-parameterized-r
description: Perform the update through the ORM, or bind every parameter if raw SQL is unavoidable.
---

# T7359: Prevent SQL injection with ORM queries and parameterized raw SQL (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7359](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7359/)
**Priority:** 10

**Finding:** Raw SQL is assembled with f-string interpolation instead of bound parameters or the ORM.

**Code to Fix:**
```python
# app/apis/orders/services/get_order_status.py lines 36-42
    raw_sql = f"""
        UPDATE orders 
        SET status = '{status_value}'
        WHERE id = {order_id}
    """
    db.execute(text(raw_sql))
    db.commit()
```

**Required Fix:**
```python
# app/apis/orders/services/get_order_status.py
db_order.status = OrderStatus(delivery_data["status"])
db.add(db_order)
db.commit()

# Parameterized equivalent if raw SQL is required:
# db.execute(
#     text("UPDATE orders SET status = :status WHERE id = :order_id AND user_id = :user_id"),
#     {"status": db_order.status.value, "order_id": order_id, "user_id": current_user.id},
# )
```

**Success Criteria:**
- No f-string or concatenation appears inside a text() call.
- External values are validated against the enum before they reach the database.
- The update is additionally scoped to the owning user.

**Status:** Applied
