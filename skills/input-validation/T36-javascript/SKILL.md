---
name: escape-untrusted-data-in-html-and-scripts
description: Escape untrusted data in HTML, attributes, CSS, and JavaScript to prevent XSS; use when untrusted input is rendered into web pages or inline scripts/styles
---

# Escape untrusted data in HTML, HTML attributes, CSS, and JavaScript

## What This Skill Does
Applies context-aware output encoding wherever untrusted data is written into HTML, HTML attributes, CSS, or JavaScript so the browser treats it as data instead of executable markup or script. This prevents cross-site scripting (CWE-79 / P632) in server-rendered templates and string-built HTML/JS/CSS.

## Decision Table
| Situation | Action |
|-----------|--------|
| Untrusted data is inserted between HTML tags (e.g., `<div>${user}</div>`) | Wrap the value with an HTML text encoder (e.g., `encodeForContext(user, 'html')`) before interpolation |
| Untrusted data is inserted into an HTML attribute value (e.g., `alt="${user}"`, `data-*`, `style=...`) | Use an attribute encoder for the attribute value and CSS encoder for any user-influenced style fragments |
| Untrusted data is embedded inside a JavaScript string literal (inline `<script>` or `onclick="..."`) | Encode with a JavaScript string encoder (e.g., `encodeForContext(user, 'js')`) and avoid mixing it into executable code paths |
| Untrusted data is written into CSS (inline `style` or `<style>` rules, class name fragments, theme names) | Encode with a CSS-safe encoder (e.g., `encodeForContext(user, 'css')`) before inserting into selectors or values |
| Framework/template engine already auto-escapes HTML and there is no manual raw output (`| raw`, `v-html`, `dangerouslySetInnerHTML`, etc.) | Prefer no change; only add encoding where auto-escaping is bypassed or non-HTML contexts (JS/CSS) are involved |

## Boundaries

### Can Do
- Detect and fix obvious XSS sinks where untrusted data is concatenated into HTML, attributes, CSS, or JS strings.
- Introduce or wire up a central `encodeForContext` helper (or framework equivalent) and apply it consistently.
- Replace manually concatenated HTML/JS/CSS with context-encoded output while preserving functional behavior.

### Cannot Do
- Cannot guarantee safety of complex third-party widgets or libraries that build DOM/JS/CSS internally.
- Cannot replace the need for other XSS defenses (CSP, sandboxing, input validation, template engine configuration).
- Cannot reliably secure code that uses APIs executing raw strings (`eval`, `new Function`, `innerHTML` with HTML fragments) without a broader refactor.

## Gotchas
- Treating all contexts the same: Using HTML encoding for JS or CSS contexts can still allow XSS because escaping rules differ per context.
- Double-encoding values: Encoding data that is already auto-escaped by the template engine can lead to broken UI (`&amp;lt;`); check whether auto-escaping is active before adding manual encoding.
- Ignoring error/debug output: Error messages, stack traces, and logs rendered in HTML that include user input must also go through an HTML encoder or they become XSS sinks.

## Quick Verification
```bash
# 1) Run the demo app (adjust file name/path as needed)
node app_fix_human_code.js

# 2) Visit the search route with an XSS payload in the browser:
#    http://localhost:3000/search?q=<img src=x onerror=alert(1)>

# 3) Confirm:
#    - No alert box appears
#    - View Source shows the payload encoded (e.g., &lt;img src=x onerror=alert(1)&gt;)

# 4) CLI-based check (no browser):
node app_fix_human_code.js "<img src=x onerror=alert(1)>" | sed -n '1,120p'

# Ensure the printed HTML contains only encoded characters for <, >, ", ', / and script does not execute.
```