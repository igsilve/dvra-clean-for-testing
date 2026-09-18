---
name: mitigate-server-side-request-forgery
description: "Harden JavaScript outbound HTTP(S) requests against SSRF by validating parsed URLs, allowlisting destinations, and sanitizing relayed responses. Use when user input can influence server-side fetches or upstream responses are returned to clients."
---
# Mitigate Server Side Request Forgery

## What This Skill Does
This skill fixes SSRF in JavaScript by replacing direct user-controlled outbound requests with a single validated request path: parse URLs with the WHATWG `URL` parser, allow only `http:` and `https:`, require an explicit hostname and port allowlist, resolve DNS and reject blocked/internal IPs, and sanitize any upstream response before relaying it. It also helps detect unsafe call sites that still use raw `http`, `https`, `fetch`, or legacy `url.parse` behavior without the SSRF guard.

## Decision Table
| Situation | Action |
|-----------|--------|
| User input, request data, env vars, CLI args, or DB values can influence an outbound URL | Apply a central SSRF-safe wrapper that parses once, validates scheme/host/port/resolved IP, and uses the same parsed values for the request |
| Code uses `url.parse(...)` or raw string checks for URL validation | Replace with the WHATWG `URL` parser and validate normalized components, not the raw string |
| Code uses `http.get`, `https.get`, `http.request`, `https.request`, or `fetch` directly with untrusted URLs | Route the call through a guarded helper such as `safeRequest` or `fetchAllowlistedUrl` |
| Upstream responses are sent back to clients | Enforce content-type and size limits, return only approved fields, and suppress raw upstream headers/errors |
| Outbound request code already uses one validated wrapper with scheme, allowlist, DNS/IP checks, and response sanitization | No action needed |

## Boundaries

### Can Do
- Add a central JavaScript helper such as `safeRequest`, `safeFetchUrl`, or `fetchAllowlistedUrl` for SSRF-safe outbound HTTP(S)
- Replace legacy `url.parse` and raw URL checks with `new URL(...)` normalization and validation
- Add response filtering so relayed upstream data is size-limited, type-checked, and transformed before return

### Cannot Do
- Infer a correct production allowlist of hostnames, CIDRs, and ports without project-specific requirements
- Guarantee network-layer protections such as firewall, proxy, service mesh, or cloud metadata blocking
- Prove every redirect, DNS rebinding case, or third-party client library behavior is safe unless all outbound paths use the guarded wrapper

## Gotchas
- Validating the raw input but requesting a rebuilt or different URL later: this creates parser mismatch bugs and can bypass checks
- Allowlisting only hostnames without validating resolved IP addresses: DNS can resolve an allowed name to loopback, link-local, or private addresses
- Sanitizing only success responses: upstream errors, headers, redirects, or oversized bodies can still leak internal details if not handled uniformly

## Quick Verification
```bash
# Confirm a central SSRF guard exists
rg -n "\b(safeRequest|safeFetchUrl|fetchAllowlistedUrl|parseAndValidateProtocol|normalizeAndValidateUrl|resolveAndValidate)\b" .

# Find likely unguarded dangerous outbound request APIs
rg -n "\b(http\.get|https\.get|http\.request|https\.request|fetch)\s*\(" . \
  -g '!node_modules' -g '!dist' -g '!build'

# Find legacy URL parsing or raw URL handling that should be reviewed
rg -n "\burl\.parse\s*\(|new URL\s*\(" . \
  -g '!node_modules' -g '!dist' -g '!build'

# Build + test using the available JavaScript toolchain for this repo
npm test || yarn test || pnpm test

# If the project has a build step, run it too
npm run build || yarn build || pnpm build || true
```