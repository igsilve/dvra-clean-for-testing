---
name: make-authorization-decisions-using-full-context
description: Use when Python code makes authorization decisions with partial identity or resource data and must require a complete server-derived authorization context at the enforcement point.
---
# Make authorization decisions using full context

## What This Skill Does
This skill fixes insufficient authorization checks caused by missing actor or resource information. It updates Python code so protected operations receive one complete, server-derived authorization context object and evaluate access using both actor attributes and trusted resource attributes at the exact layer that returns or mutates protected data. It also preserves end-user context across service boundaries when downstream code performs the authorization check.

## Decision Table
| Situation | Action |
|-----------|--------|
| Protected function reads, returns, updates, or deletes sensitive data using only `document_id`, `user_id`, `username`, `role`, or request parameters | Apply this fix |
| Authorization inputs are scattered across multiple parameters or reconstructed from globals/session/request state | Replace with a single required immutable `AuthzContext`-style object |
| Authorization checks use client-supplied owner, tenant, or scope values instead of trusted server-side resource data | Load the target resource from a trusted source first and authorize against both actor and resource |
| A downstream service or repository makes the authorization decision | Forward end-user authorization context in a structured form and reconstruct it before the check |
| Code already requires full server-derived actor context and trusted resource context at the enforcement point | No action needed |

## Boundaries

### Can Do
- Refactor Python service, model, repository, and helper functions to require a complete authorization context input
- Replace partial authorization checks with checks that compare actor context to trusted resource attributes
- Add validation for missing or malformed authorization context and preserve end-user context across service calls

### Cannot Do
- Invent correct authorization rules, roles, tenant semantics, or ownership policy without evidence from the codebase
- Prove distributed callers actually authenticate or sign propagated context unless that mechanism already exists
- Guarantee security if other code paths still access the same protected resource without the required context

## Gotchas
- Passing only `user_id` or `role`: this is still incomplete because ownership, tenant, scopes, and other required attributes may be missing
- Trusting request JSON, headers, or query parameters for `owner`, `tenant_id`, or `role`: these are client-controlled and cannot replace server-derived authorization attributes
- Adding checks only in controllers: deeper service or repository functions may still be called directly and bypass authorization if they do not require context

## Quick Verification
```bash
# Confirm a required authz context or equivalent guard exists in protected code
rg -n "class AuthzContext|@dataclass\(frozen=True\)\s*class AuthzContext|def .*?\((ctx|authz_context|user): .*?, document_id: str\)" .

# Find likely unguarded dangerous access patterns that bypass full-context authorization
rg -n "def (fetch|get|read|update|delete)_[a-z_]*\((document_id|resource_id|user_id): .*?\):|return document\.content|\.content\s*=|DOCUMENTS\[[^\]]+\]" .

# Build + test using common Python toolchain commands; run what exists
python -m compileall .
pytest -q
python -m unittest discover
```