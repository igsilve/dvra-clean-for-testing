---
name: avoid-dom-based-xss
description: Avoid DOM-based Cross-Site Scripting by replacing unsafe DOM sinks, forbidding executable attributes, and encoding URLs/CSS; Use when untrusted DOM values reach innerHTML/document.write/event attributes or URL/style contexts.
---

# Avoid DOM-based Cross-Site Scripting (XSS)

## What This Skill Does
Prevents DOM-based XSS where attacker-controlled values from browser/DOM sources (like `location`, query params, `referrer`, or other client data) are written into HTML, attributes, URLs, CSS, or script-like strings without proper handling. It guides you to replace unsafe sinks (`innerHTML`, `document.write`, executable attributes) with safe DOM APIs, apply allow-lists for attributes, and use context-appropriate encoding and URL validation.

## Decision Table
| Situation | Action |
|-----------|--------|
| Code writes values from `location`, `referrer`, query/hash, or other untrusted DOM data into `innerHTML`, `outerHTML`, or `document.write` | Replace with `textContent` / `innerText` and safe DOM construction (`createElement`, `appendChild`) so the browser never parses user data as HTML |
| Code sets event handler attributes or executable attributes (e.g., `onclick`, `onload`, `srcdoc`) using untrusted data | Forbid these: remove data-driven handler attributes and use static event listeners (`addEventListener`) with untrusted values treated as data only |
| Code builds URLs or CSS `url()` values from untrusted data (`href`, `src`, `background-image`) | Normalize and validate via an allow-list of schemes (`http`, `https`, same-origin), use `new URL` and encode user-controlled components; block or empty dangerous schemes like `javascript:` or `data:` |
| Code uses untrusted DOM values in script-like strings (`eval`, `new Function`, string-based `setTimeout`/`setInterval`, inline `<script>`) | Remove string-based code execution; pass functions instead, or treat values as plain text and write them via `textContent` or logging only |
| Review shows data is already handled via safe DOM APIs (`textContent`, attribute allow-list, validated URLs, no executable attributes) | No action needed; keep current pattern and document it as the project’s safe standard |

## Boundaries

### Can Do
- Detect and refactor obvious DOM XSS sinks using `innerHTML`, `outerHTML`, `document.write`, and event attributes fed by untrusted input.
- Introduce safe DOM construction (using `createElement`, attribute setters for non-executable attributes, `appendChild`, `textContent`).
- Add helpers for safe URL building and CSS `url()` composition with scheme allow-lists and proper encoding.

### Cannot Do
- Cannot guarantee HTML or URL libraries you add are themselves secure without human review of their documentation and defaults.
- Cannot infer complex application-level trust boundaries (e.g., which inputs are fully trusted admin-only fields) without explicit hints in code or comments.
- Cannot prevent server-side or stored XSS; this skill only addresses client-side / DOM-based injection patterns in browser-executed code.

## Gotchas
- Assuming `innerHTML` is safe after “sanitizing” input with ad-hoc string replaces: attackers often bypass naive filters; prefer `textContent` or robust, vetted sanitization libraries plus safe DOM APIs.
- Allowing all attributes except those starting with `on`: other attributes (like `srcdoc`, `href` with `javascript:`, `xlink:href`) can still execute code; use a strict allow-list of known-safe attributes instead of a loose block-list.
- Treating URL encoding as enough without checking protocol: `encodeURIComponent('javascript:alert(1)')` is still dangerous if you decode or concatenate into `href` without enforcing allowed schemes.

## Quick Verification
```bash
# Run the vulnerable app (before fix) and observe XSS
node app_vulnerable_code.js  '<img src=x onerror=alert(1)>' &
VULN_PID=$!
sleep 1
echo "Open http://localhost:3000/profile?fragment=%3Cimg%20src%3Dx%20onerror%3Dalert(1)%3E in a browser and confirm alert fires"

# Run the fixed app and verify no script execution
node app_fix_original_code.js  '<img src=x onerror=alert(1)>' &
FIX_PID=$!
sleep 1
echo "Open http://localhost:3000/profile?fragment=%3Cimg%20src%3Dx%20onerror%3Dalert(1)%3E in a browser and confirm it renders as inert text and no alert fires"

# Basic static sanity check: ensure no unsafe sinks remain in the fixed file
grep -nE 'innerHTML|outerHTML|document\.write|setAttribute\\(.*on[a-zA-Z]+|eval\\(|new Function\\(|setTimeout\\(|setInterval\\(' app_fix_original_code.js || echo "No obvious DOM XSS sinks found in fixed file"

# Clean up background processes (optional)
kill $VULN_PID $FIX_PID 2>/dev/null || true
```