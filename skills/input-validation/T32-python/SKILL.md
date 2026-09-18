---
name: always-perform-input-validation-on-a-server
description: Use when Python code processes client-controlled input on the server and must enforce centralized validation, failure logging, and generic error responses before business logic runs.
---
# Always Perform Input Validation on a Server

## What This Skill Does
This skill fixes improper input validation in Python by ensuring every server-controlled entry point validates untrusted input before parsing, conversion, persistence, or business logic. Apply it when request parameters, JSON fields, form values, CLI arguments, message payloads, or other external inputs are trusted too early. The fix centralizes reusable validation, rejects invalid or unexpected input early, logs validation failures with bounded structured details, and returns only a generic error message to callers.

## Decision Table
| Situation | Action |
|-----------|--------|
| Request handlers, CLI entry points, workers, or helpers use external input before checks | Add a server-side validator and call it before any `int()`, `float()`, indexing, persistence, or business logic |
| The same field or payload shape is validated in multiple places | Centralize validation in a reusable function such as `validate_quantity()` and reuse it across all entry points |
| Validation failures return detailed rule information to the client | Replace with one generic response such as `{"error": "Invalid input."}` and keep specifics only in logs |
| Validation failures are not logged or logs include raw attacker input | Add structured logging with timestamp, source IP if available, event, and error code; avoid raw untrusted values |
| Code already validates type, required fields, length, range, format, and allowed values before use | No action needed |

## Boundaries

### Can Do
- Add server-side validation functions for Python inputs before parsing or business logic
- Centralize generic validation error responses and structured validation-failure logging
- Refactor common flows so validated values are parsed only after validation succeeds

### Cannot Do
- Infer full business rules or allowed value sets that are not defined by the application
- Guarantee downstream safety from SQL injection, XSS, or authorization flaws by validation alone
- Replace schema design, output encoding, database constraints, or access control checks

## Gotchas
- Validating only in the browser or client: attackers can bypass client checks and send crafted requests directly to the server
- Logging raw invalid input: this can create log injection, oversized logs, or accidental storage of sensitive data
- Returning detailed validation errors to callers: this reveals internal rules and helps attackers refine payloads

## Quick Verification
```bash
# Confirm reusable server-side validation or generic error helpers exist
rg -n "def validate_[a-zA-Z0-9_]+\(|GENERIC_VALIDATION_ERROR|def validation_error_response\(|def log_validation_failure\(" .

# Find likely unguarded dangerous conversions/usages of external input that should be preceded by validation
rg -n "int\(|float\(|json\.loads\(|pickle\.loads\(|ast\.literal_eval\(" .

# Build/test check for common Python project layouts
python -m compileall . && (python -m pytest -q || python -m unittest discover -v)
```