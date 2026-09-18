---
name: mitigate-server-side-request-forgery
description: Mitigate Server Side Request Forgery (SSRF) by validating/whitelisting outbound URLs and restricting access to internal services; Use when server code makes HTTP(S) requests influenced by user input
---

# Mitigate Server Side Request Forgery

## What This Skill Does
Prevents Server Side Request Forgery (SSRF) by hardening any server-side HTTP client that uses user-influenced URLs, hosts, or ports. It introduces strict allowlists, URL scheme restrictions, IP/DNS checks, and response sanitization so attackers cannot pivot to internal services, metadata endpoints, or arbitrary hosts, and cannot exfiltrate sensitive internal data via upstream responses.

## Decision Table
| Situation | Action |
|-----------|--------|
| Server code builds an outbound URL directly from request input (query/body/header/path/argv) | Replace with a validated URL flow: parse via `URL`, apply protocol restriction, enforce hostname/port allowlist, and centralize checks in a helper (e.g., `validateAndResolveUrl` / `robustFetch`) |
| Code lets users specify full URLs for “proxy”, “webhook tester”, “URL preview”, or “fetch arbitrary URL” features | Replace free-form URL usage with: strict domain/host allowlist, HTTP(S)-only enforcement, DNS/IP validation rejecting private/loopback/link-local ranges, and generic error messages |
| Application exposes internal services (metrics, status, metadata, admin APIs) by taking a URL from users | Refactor to an operation-based API (fixed map of operations → fixed URLs) where user input only affects whitelisted query/path parameters, never host/protocol/port |
| Upstream HTTP responses (from internal or third-party services) are forwarded directly to the client (headers + body) | Insert a sanitization layer: cap response size, restrict content types, whitelist JSON fields, remove or rewrite sensitive headers, and avoid echoing raw errors |
| Outbound client already uses: strict host allowlist, HTTP(S)-only, blocked private IP ranges, and response filtering | No action needed; keep configuration in a central request layer and ensure new callers reuse it |

## Boundaries

### Can Do
- Detect and refactor obvious SSRF sinks where URLs/hosts/ports are built from user input (HTTP APIs, CLI args, config values).
- Introduce centralized outbound request helpers that enforce allowlists, protocol restrictions, and DNS/IP validation before any HTTP(S) call.
- Add response-sanitization layers that limit what upstream data and headers are exposed to callers.

### Cannot Do
- Automatically derive a correct allowlist of safe destinations; a human must decide which hosts/domains/IP ranges are business-necessary.
- Guarantee protection against every environment-specific edge case (e.g., unusual internal IP ranges, custom DNS, non-HTTP protocols) without additional human review.
- Retrofit protections into third-party binaries, external services, or infrastructure components that are not part of the visible codebase.

## Gotchas
- Assuming validation on the initial URL is enough: skipping checks after redirects lets attackers bounce through an allowed host to a blocked internal IP or protocol.
- Relying only on hostname checks: DNS rebinding or internal DNS can map allowed hostnames to private or loopback IPs; always validate the resolved IPs and block private/link-local/loopback ranges unless explicitly whitelisted.
- Exposing raw upstream errors and headers: even with outbound restrictions, leaking stack traces, server versions, or internal IPs in error messages or headers provides valuable information for attackers.

## Quick Verification
```bash
# 1) Basic SSRF rejection: internal metadata / localhost / private ranges
node app_fix_original_code.js "http://169.254.169.254/latest/meta-data/" || true
node app_fix_original_code.js "http://127.0.0.1:80/" || true
node app_fix_original_code.js "http://192.168.0.10/" || true

# 2) Scheme restriction check
node app_fix_original_code.js "file:///etc/passwd" || true

# 3) Allowed external host still works (per ALLOWED_DESTINATIONS)
node app_fix_original_code.js "https://example.com"

# 4) HTTP API tests (requires app running on PORT, default 3000)
# Allowed external fetch should succeed
curl -s -X POST http://localhost:3000/fetch \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'

# SSRF-style payloads should be blocked with generic errors / 4xx/403
curl -i -X POST http://localhost:3000/fetch \
  -H "Content-Type: application/json" \
  -d '{"url":"http://169.254.169.254/latest/meta-data/"}'

curl -i -X GET http://localhost:3000/internal-metadata
```