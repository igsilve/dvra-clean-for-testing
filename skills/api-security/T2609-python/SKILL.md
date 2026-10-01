---
name: verify-result-set-size-returned-by-queries-are-controlled
description: Ensure database queries return bounded result sets with enforced limits, rollback, and controlled errors. Use when untrusted input can trigger large query results or sensitive bulk reads.
---

# Verify that the result set size returned by queries are controlled

## What This Skill Does
Enforces hard limits on database query result sizes so attackers or buggy features cannot pull excessive sensitive records or exhaust resources. It guides you to wrap sensitive queries in helpers that cap rows, detect overflows (using sentinel rows or incremental fetching), roll back transactions when limits are exceeded, and return standardized, non-leaky error responses.

## Decision Table
| Situation | Action |
|-----------|--------|
| Sensitive query (users, audit logs, PII, financial data) uses `fetchall()`/unbounded cursor without `LIMIT` or row-count checks | Add a hard, server-controlled max row limit and enforce it at query and/or application level |
| API/endpoint directly returns all rows from a search or listing based on user input | Introduce server-side max limit, overflow detection, and return a controlled “result set too large” error instead of full data |
| Sensitive operation runs inside a transaction and processes many rows from a query | Use a transactional helper that detects result-set overflow and rolls back on limit breach before any commit |
| Application has multiple sensitive queries each implementing limits differently | Refactor into a shared helper/abstraction that centralizes max limit, overflow error, rollback, and error mapping |
| Query already uses a strict, server-controlled `LIMIT` lower than or equal to policy and checks for overflow | No action needed, but confirm limit is not overridden by user input |

## Boundaries

### Can Do
- Detect unbounded or weakly bounded result sets (e.g., `fetchall()`, no `LIMIT`, client-controlled limits).
- Introduce or strengthen server-controlled maximum row limits with sentinel-based overflow checks.
- Add or refactor to shared helpers that encapsulate limit enforcement, transaction rollback, and error mapping.
- Convert over-limit situations into standardized, non-sensitive application errors (e.g., HTTP 413 with generic message).
- Adapt examples to common stacks (Node.js/pg, Python/sqlite3, REST APIs).

### Cannot Do
- Infer correct business-specific thresholds (e.g., whether max should be 100 vs 10,000) without project guidance.
- Replace or redesign application-wide pagination/UX patterns (e.g., infinite scroll) by itself.
- Fix unrelated database issues (SQL injection, broken auth, incorrect joins) unless clearly tied to result size control.
- Guarantee performance characteristics (e.g., optimal indexing) beyond bounding result size.
- Automatically migrate every legacy query in a large codebase without developer review and staged rollout.

## Gotchas
- Assuming client-supplied limits are safe: Letting callers set arbitrary `limit`/`page_size` and trusting it (even with a default) still allows massive results. Always enforce an internal server-side maximum (e.g., `effectiveLimit = min(requested, MAX_ROWS)`).
- Limiting only in application code but still calling `fetchall()`: Fetching all rows and then slicing in memory still causes data exposure and resource exhaustion. Apply limits at the SQL or cursor level and use sentinel rows or `fetchmany()` to detect overflow.
- Ignoring transactional consistency: When processing many rows in a transaction, failing to roll back on overflow can leave partial state changes if you commit anyway. Ensure any “too many rows” condition triggers rollback and propagates a clear error to callers.

## Quick Verification
```bash
# Python vulnerable vs fixed example

# 1) Run the vulnerable app (will return all matches).
python app_vulnerable_code.py "a"

# 2) Run the fixed app; for large datasets, it should error once > MAX_RESULTS.
python app_fix_original_code.py "a"

# Node.js (example patterns similar to HOW-TO):

# 3) Exercise a sensitive endpoint expected to cap rows (e.g., 500 max).
curl -i "http://localhost:3000/api/sensitive-users?search=a"

# - Confirm:
#   * HTTP 200 with <= configured max rows in body, OR
#   * HTTP 413 (or similar) with a generic "result_set_too_large" style error.

# 4) Force a huge result set via filters or seed data
#    and verify logs/DB show no partial transaction commits after limit breach.
```