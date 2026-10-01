---
name: protect-against-json-hijacking
description: Defend JSON APIs against JSON hijacking (P719) using session-bound URLs, nonces, safe MIME types, and top-level objects; Use when JSON endpoints may be loaded in attacker-controlled browsers
---

# Protect against JSON hijacking

## What This Skill Does
This skill helps secure JSON APIs against JSON hijacking (especially in older browsers) by making JSON endpoints hard to discover or abuse, requiring per-session nonces, enforcing safe JSON MIME types, and ensuring the top-level JSON value is an object instead of an array or executable structure. It guides when and how to apply these protections and what patterns to avoid.

## Decision Table
| Situation | Action |
|-----------|--------|
| JSON endpoint returns a top-level array (e.g., `[...]`) or primitive | Wrap the data in a top-level object (e.g., `{ "items": [...] }`) and standardize an envelope (`{ "data": ..., "meta": ... }`) |
| Sensitive JSON is exposed at a predictable, static URL (e.g., `/api/user/favorites`) | Introduce a session-bound, unpredictable JSON URL using a cryptographically strong token tied to the authenticated session |
| JSON endpoint is callable without a per-session nonce or similar secret | Add a per-session JSON nonce stored server-side and require it on all sensitive JSON requests (header or query param), rejecting missing/invalid values |
| JSON endpoint returns `text/html`, ambiguous types, or relies on content sniffing | Enforce `Content-Type: application/json` and add `X-Content-Type-Options: nosniff` for all JSON responses |
| Clients can be updated to handle wrapped JSON (comment-filtered/prefixed) | Optionally introduce comment-filtered or prefixed JSON variants, with clear content types or conventions, and require clients to unwrap before parsing |
| Endpoint already uses session-bound URLs or nonces, top-level objects, and strict JSON MIME type | No action needed; only verify behavior with attacker-style tests |

## Boundaries

### Can Do
- Detect and refactor JSON endpoints that:
  - Use top-level arrays or primitives.
  - Use predictable URLs without extra secrets.
  - Lack per-session nonces or equivalent protections.
- Add per-session, cryptographically strong tokens/nonces and validate them server-side using constant-time comparison where appropriate.
- Enforce safe JSON response headers (`application/json`, `nosniff`) and normalize top-level structures to objects/dicts.
- Introduce optional comment-filtered or prefixed JSON variants where clients can handle them.

### Cannot Do
- Cannot retrofit protections into third-party APIs or services you do not control; can only add wrappers or gateways around them.
- Cannot guarantee protection in the absence of an authentication/session mechanism or server-side state to store tokens/nonces.
- Cannot maintain or update all consuming clients; you must ensure client code is updated to:
  - Use new session-bound URLs.
  - Send required nonces.
  - Strip prefixes/wrappers when optional variants are enabled.

## Gotchas
- Assuming CSRF tokens alone fix JSON hijacking: CSRF protections often apply to state-changing requests and may not be enforced on read-only JSON GET endpoints; still require JSON-specific nonces or session-bound URLs for sensitive data.
- Forgetting to rotate or invalidate tokens/nonces on session changes: Reusing the same token/nonce across logouts, logins, or privilege changes can let old attacker-controlled contexts keep accessing new data; always regenerate/expire secrets on key auth events.
- Returning top-level arrays from "harmless" endpoints: Even if the data seems non-sensitive today, top-level arrays are easier to exploit via `<script>` inclusion; always use top-level objects to avoid unexpected data exposure when the data becomes sensitive later.

## Quick Verification
```bash
# 1. Verify unauthenticated or nonce-less access fails
curl -i https://your-app.example.com/api/secure-favorites

# 2. Initialize session-bound JSON data or nonce (after login, with cookies)
curl -i -c cookies.txt https://your-app.example.com/init-json
curl -i -c cookies.txt https://your-app.example.com/init-nonce

# 3. Call protected JSON endpoint with the correct nonce from the same session
curl -i -b cookies.txt \
  -H "X-JSON-Nonce: <value-from-init-nonce-response>" \
  https://your-app.example.com/api/secure-favorites

# 4. Confirm Content-Type and top-level object shape
curl -i https://your-app.example.com/api/items
# Check headers: Content-Type: application/json; charset=utf-8
# Check body starts with '{' and not '['

# 5. Simulate attacker-style script tag load (manual check)
# In a test HTML file, add:
#   <script src="https://your-app.example.com/api/user/favorites"></script>
# Load in an old/legacy browser and confirm no readable/global data leaks occur.
```