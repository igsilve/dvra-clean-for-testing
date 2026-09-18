---
name: bind-variables-in-sql-statements
description: Fixes SQL injection by replacing string-built queries with bound parameters; use when untrusted data flows into SQL text via concatenation, interpolation, or unsafe ORM/raw SQL APIs.
---

# Bind variables in SQL statements

## What This Skill Does
Rewrites database access so that untrusted input is always passed as bound parameters instead of being concatenated or interpolated into SQL strings. It targets SQL injection risks (CWE-89) in direct driver calls, raw SQL in ORMs, and stored procedure invocations, and adds strict validation only for parts that cannot be parameterized (like column names or sort directions).

## Decision Table
| Situation | Action |
|-----------|--------|
| SQL query string is built with `+`, `f"..."`, `%`, `.format()`, or template literals including untrusted data | Replace with a static SQL template and pass all untrusted values as bound parameters/placeholders |
| ORM or query builder exposes a "raw SQL" or `text()` API and untrusted data is interpolated into the SQL text | Use the ORM's parameter binding (`:name`, `?`, `$1`, etc.) and supply values via the ORM's parameter dict/args |
| Stored procedure calls are constructed as strings (e.g., `"CALL proc('" + user + "')"`) | Switch to the driver's parameterized procedure call API (e.g., `callproc`, parameter arrays) and bind arguments |
| Dynamic identifiers (table/column names, sort direction) must come from user input and cannot be bound | Implement whitelist-based validation/mapping and only interpolate validated identifiers; keep data values parameterized |
| Code already uses parameterized queries with no user-controlled SQL fragments | No action needed |

## Boundaries

### Can Do
- Detect and refactor string-built SQL that embeds untrusted input in application code.
- Convert common driver and ORM patterns (e.g., `sqlite3`, SQLAlchemy, MySQL connectors) to use bound parameters.
- Introduce helper functions or data-access layers that enforce parameter binding consistently.
- Add whitelist validation for non-parameterizable parts (identifiers, sort direction) while keeping data values bound.
- Suggest basic runtime tests using obvious injection payloads to confirm behavior.

### Cannot Do
- Change how the underlying database engine itself parses SQL (this is entirely application-side).
- Automatically verify that every ORM abstraction truly sends prepared/parameterized statements over the wire (requires runtime inspection/logging).
- Secure dynamic SQL that fundamentally depends on free-form user-provided SQL fragments (e.g., user-supplied WHERE clauses) without changing the feature design.
- Guarantee safety if other layers (stored procedures, views, triggers) also build SQL dynamically from untrusted data that is not visible in the current codebase.
- Replace business-specific validation or complex query-building logic with fully generic solutions.

## Gotchas
- Assuming stored procedures are always safe: they are still vulnerable if the procedure itself concatenates parameters into dynamic SQL; binding must occur in the procedure or its callers, not just because it's a "stored procedure."
- Relying only on escaping or input sanitization instead of binding: escaping is error-prone and DB-specific; always prefer parameter binding and use validation only for the few things that cannot be parameterized (like column names).
- Mixing secure and insecure patterns in the same query: binding some parameters while still concatenating another untrusted fragment (like a filter or limit) leaves the query exploitable.
- Trusting ORM "convenience" methods that accept raw SQL strings with formatted input: even when using an ORM, any path that accepts raw SQL must still use placeholder syntax and bound parameters.

## Quick Verification
```bash
# Example using the provided vulnerable script (Python + sqlite3)

# 1. Run the vulnerable version and observe injection
python app_vulnerable.py "alice' OR '1'='1"
# Expectation (vulnerable): returns multiple users or all rows

# 2. Run the fixed/parameterized version and confirm no injection
python app_fixed.py "alice' OR '1'='1"
# Expectation (safe): returns at most the real 'alice' row; no extra rows

# 3. Try a destructive-style payload and confirm it is treated as data
python app_fixed.py "bob'; DROP TABLE users; --"
# Expectation: no errors about missing tables; DB remains intact

# 4. If using an ORM with SQL logging enabled, confirm that:
#    - SQL statements contain placeholders
#    - Data values are sent separately, not interpolated into the SQL text
```