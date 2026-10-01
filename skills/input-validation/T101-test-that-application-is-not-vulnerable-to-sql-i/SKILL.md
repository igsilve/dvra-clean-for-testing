---
name: t101-test-that-application-is-not-vulnerable-to-sql-injection
description: Replace the interpolated UPDATE with a parameterized statement so no value can alter the query structure.
---

# T101: Test that application is not vulnerable to SQL injection

**Category:** CODE_FIX
**SD Elements:** [T101](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T101/)
**Priority:** 10

**Finding:** The UPDATE statement is built by f-string interpolation of status_value and order_id and executed through text(), so it is directly injectable.

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

# If raw SQL is genuinely required, bind every value:
# db.execute(
#     text("UPDATE orders SET status = :status WHERE id = :order_id"),
#     {"status": OrderStatus(status_value).value, "order_id": order_id},
# )
```

**Success Criteria:**
- No SQL string in the codebase is built with f-strings, concatenation or % formatting.
- The status value is validated against the OrderStatus enum before use.
- A delivery response containing `'; DROP TABLE orders; --` leaves the schema intact.

**Status:** Applied
