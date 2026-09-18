---
name: escape-untrusted-data-in-html-html-attributes-css-and-javascript
description: Escape untrusted data in HTML, attributes, CSS, and JavaScript to prevent XSS (CWE-79); use when user-controlled or external data is written into web pages
---

# Escape untrusted data in HTML, HTML attributes, CSS, and JavaScript

## What This Skill Does
Fixes cross-site scripting (XSS) by ensuring any untrusted data (user input, headers, cookies, upstream responses, CLI args, etc.) is **contextually escaped right before it is written into HTML, HTML attributes, CSS, or JavaScript**. Prefers using templating engines with auto-escaping and small helper functions to centralize encoding.

## Decision Table
| Situation | Action |
|-----------|--------|
| Untrusted data is interpolated into HTML body (e.g., `<p>{query}</p>`) | Escape using HTML-encoding (`<` → `&lt;`, `"` → `&quot;`) or rely on template engine auto-escaping; replace raw interpolation with escaped value |
| Untrusted data is placed in HTML attributes (`<a href="{url}">`, `<input value="{name}">`) | Escape with HTML attribute encoding (also encode quotes); avoid `javascript:` URLs and event handler attributes entirely |
| Untrusted data appears inside inline JS (`<script>var x = '{value}';</script>`) | Avoid inline JS where possible; if unavoidable, JavaScript-encode the value and ensure it cannot break out of string/JSON context |
| Untrusted data appears in inline CSS (`style="color:{color}"` or `<style>.x{ background:url({u}) }</style>`) | Prefer predefined classes; otherwise CSS-encode and restrict to safe patterns (e.g., whitelist colors), never allow `url(javascript:...)` |
| UI or error pages render messages containing user-controlled data (query params, form fields, upstream error text) | Run all such text through the same HTML-context escaping used for normal content; do not render raw exception or request values |
| Templating engine already has auto-escaping enabled and no `safe`/`raw` overrides are used | No action needed beyond verifying no bypasses of auto-escaping in risky places |

## Boundaries

### Can Do
- Identify typical XSS sinks where untrusted data goes directly into HTML, attributes, inline CSS, or JS.
- Replace vulnerable interpolations with context-appropriate escaping or safe template constructs.
- Introduce or use centralized helper functions for escaping per context (HTML, attribute, JS, CSS).
- Enable or rely on template engine auto-escaping and remove unnecessary `|safe`/`raw` usages.
- Fix error pages so they encode any user-controllable data before display.

### Cannot Do
- Cannot fully protect pages that rely on dangerous patterns like `innerHTML`/`document.write` or heavy inline event handlers without broader refactoring.
- Cannot fix DOM-based XSS that happens entirely on the client side (JavaScript manipulating the DOM) unless that code is provided and in scope.
- Cannot choose or enforce CSP, sandboxing, or HTTP security headers; this skill focuses on **encoding**, not all XSS defenses.
- Cannot safely "sanitize" arbitrary HTML-rich user content (e.g., WYSIWYG posts) without a dedicated HTML sanitizer and clear allowed tags.
- Cannot guarantee framework-specific best practices beyond generic escaping patterns if the framework's templating/escaping model is not shown.

## Gotchas
- Treating input as "validated" instead of "escaped": Validation (length, charset, pattern) **does not replace** contextual escaping. You still must escape at output time.
- Escaping at input/storage time: Encoding data when you store it and then re-encoding or reusing it in other contexts leads to double-encoding or missed contexts; always escape **right before rendering** in the specific output context.
- Using HTML escaping for non-HTML contexts: HTML encoding is not sufficient for JavaScript strings, JSON, or CSS; each context has different characters that must be encoded to prevent breaking out into executable code.
- Disabling or bypassing auto-escaping (`|safe`, `|raw`, `dangerouslySetInnerHTML`, etc.) for convenience: This often reintroduces XSS; only bypass auto-escaping for truly trusted content and document why.
- Rendering raw error messages or stack traces that may include user input: These must be passed through the same HTML escaping as any other user-controlled text before being shown in the browser.

## Quick Verification
```bash
# 1. Basic reflected XSS test for HTML body context
curl "http://localhost:5000/search?q=<script>alert(1)</script>" -v

# Confirm in the browser/devtools:
# - The response contains &lt;script&gt;alert(1)&lt;/script&gt; (or similar)
# - No alert box or script execution occurs

# 2. Attribute-context test (if applicable)
curl "http://localhost:5000/?name=\" onmouseover=\"alert(2)" -v
# Check the rendered HTML:
# - Quotes and angle brackets in the name are encoded
# - The HTML structure is intact and no new event handler appears

# 3. Error-page test where request data is echoed
curl "http://localhost:5000/some-endpoint?input=<img src=x onerror=alert(3)>" -v
# Verify:
# - The tag appears as text (e.g., &lt;img ...) in the error page
# - No image loads and no alert executes
```