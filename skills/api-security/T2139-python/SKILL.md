---
name: prevent-information-exposure-through-apis
description: Prevents APIs from leaking sensitive or internal fields by enforcing minimal, schema-validated responses; use when endpoints return whole objects or lack explicit response shaping.
---

# Prevent information exposure through APIs

## What This Skill Does
Reduces information exposure in APIs by replacing "return full object" patterns and generic serializers with explicit, minimal response shapes, enforcing per-endpoint schemas (including errors), and aligning returned fields with authorization rules. It also removes dead/unused endpoints to shrink attack surface, ensuring clients can't extract sensitive or internal data by calling APIs directly.

## Decision Table
| Situation | Action |
|-----------|--------|
| API handler returns `asdict()` / ORM model / full object directly | Introduce a per-endpoint response mapper that only returns needed, non-sensitive fields |
| Endpoint returns more fields than documented or includes secrets (passwords, API keys, SSNs, tokens, internal flags) | Define a minimal response model and strip/deny sensitive or undocumented fields before serialization |
| API uses a generic serializer (e.g., `.to_dict()`, `.schema()`, auto-JSON) for responses | Replace with explicit serializers or view-model builders that project only allowed fields |
| No explicit response schema exists (especially for error responses) | Define and enforce response schemas, rejecting or removing unexpected keys and invalid types |
| Responses differ based on user role/permissions | Add role/authorization-aware field whitelists and ensure only allowed fields reach the client |
| Endpoint or route is no longer used or is "temporarily disabled" | Remove the handler or return a minimal generic 404/410 without internal details |

## Boundaries

### Can Do
- Identify and refactor patterns where APIs return full database records or domain objects directly.
- Introduce explicit per-endpoint response builders / DTOs and central sensitive-field lists.
- Add or tighten response schemas (including errors) and basic schema validation hooks.
- Implement whitelist-based field filtering by endpoint and/or role.
- Suggest removal or hard-disable of unused or debug endpoints that expose internal details.

### Cannot Do
- Infer business-specific authorization rules or which fields are legally/compliantly sensitive without hints from code or comments.
- Guarantee no data exposure from third-party libraries, proxies, or layers not visible in the project.
- Configure infrastructure-level protections (API gateway redaction, WAF rules, logging scrubbing) beyond code changes.
- Rewrite entire API designs or versions; focuses on hardening existing handlers and serializers.
- Automatically align with external specs (OpenAPI, GraphQL schema) if they're missing or inconsistent; needs developer confirmation.

## Gotchas
- Assuming client-side filtering is enough: Hiding fields in the UI does not protect against direct API calls; responses themselves must be safe before serialization.
- Over-relying on "blacklist" removal of sensitive fields: It's easy to forget to add new sensitive attributes. Prefer explicit per-endpoint/role whitelists or schemas as the primary control.
- Forgetting error and fallback paths: Handlers may leak internal messages, stack traces, or raw records in error responses; define and validate schemas for errors too.

## Quick Verification
```bash
# 1. Run tests (adjust command to your project)
pytest -k "api or information_exposure or user_profile" -q

# 2. Manually hit a previously vulnerable endpoint
curl -i http://localhost:5000/user/1

# Confirm the JSON does NOT contain:
# - password_hash
# - ssn
# - api_key
# - any undocumented/internal fields

# 3. (If schemas added) Run schema or type checks
mypy . || true
pytest -k "schema or response_validation" -q

# 4. Probe removed/deprecated endpoints
curl -i http://localhost:5000/internal/debug-user/1
# Expect 404/410 with minimal, generic body and no internal details
```