---
name: avoid-untrusted-server-side-selection
description: "Prevent server-side page, view, template, and include selection from untrusted input in JavaScript. Use when request or CLI data influences fs/path-based resource selection or template/view names."
---
# Avoid Untrusted Data for Server-Side Selection

## What This Skill Does
This skill fixes cases where untrusted input is used to choose a server-side page, view, template, include target, or file. In JavaScript, this often appears as request data or CLI arguments being concatenated into template names, file paths, or `res.render()` selectors. The fix is to validate type, enforce a strict whitelist and small maximum length, then resolve input only through a server-controlled immutable allowlist of permitted resources, rejecting unknown values without fallback.

## Decision Table
| Situation | Action |
|-----------|--------|
| Request data, route params, query params, body fields, headers, env vars, or CLI args are concatenated into template names, file names, include paths, or `res.render()` values | Apply this fix |
| Code uses `fs.readFileSync`, `fs.readFile`, `path.join`, `path.resolve`, or `res.render` with user-controlled selectors | Replace direct selection with a frozen mapping or explicit allowed set |
| Selector is intended to choose one of a small known set such as `home`, `about`, or `profile` | Add type check, strict whitelist regex, max length check, and allowed-set membership check |
| Code already uses a server-controlled immutable mapping and rejects unknown, non-whitelisted, or oversized values | No action needed |
| Code falls back to a default page when validation fails | Reject the input instead of silently selecting a resource |

## Boundaries

### Can Do
- Replace direct server-side resource selection with a fixed server-controlled mapping
- Add strict selector validation for type, format, length, and allowed values
- Find common JavaScript danger patterns involving `fs`, `path`, and template rendering APIs

### Cannot Do
- Guarantee safety if other code later uses the validated value to build new paths or dynamic includes
- Infer the correct business allowlist without project knowledge of valid pages or templates
- Fix client-side template injection or unrelated file access issues outside the selection flow

## Gotchas
- Validating with a loose regex only: this is wrong because `admin` may match the format but still be an unapproved selector unless checked against an explicit allowed set
- Falling back to `home` on invalid input: this is wrong because it hides attacks and still performs server-side selection instead of rejecting unsafe input
- Using `path.join(viewsDir, userInput + '.html')` after validation alone: this is wrong because selection should come from a server-defined mapping, not directly from user data

## Quick Verification
```bash
# Confirm a guard or allowlist exists
rg -n "Object\.freeze|new Set\(|ALLOWED_[A-Z_]+|TEMPLATE_MAP|PAGE_NAME_PATTERN|isAllowed[A-Z]\w+" .

# Find likely unguarded dangerous server-side selection patterns
rg -n "res\.render\s*\(\s*(req|request|ctx|argv|process\.argv)|fs\.(readFileSync|readFile)\s*\(\s*path\.(join|resolve)\([^)]*(req|request|ctx|argv|process\.argv)|path\.(join|resolve)\([^)]*(req\.|request\.|ctx\.|argv|process\.argv)" .

# Build + test using whichever JavaScript toolchain the project provides
npm test || yarn test || pnpm test || bun test
```