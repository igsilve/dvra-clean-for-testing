---
name: prevent-server-side-template-injection-ssti
description: Hardens template usage to prevent Server-Side Template Injection (SSTI) and Improper Neutralization of SSI; use when untrusted input reaches server-side template engines.
---

# Prevent Server-Side Template Injection (SSTI)

## What This Skill Does
Detects and fixes patterns where untrusted input is interpreted as template syntax by server-side template engines (e.g., Jinja2), leading to Server-Side Template Injection (SSTI). It guides the assistant to replace unsafe template construction and rendering with sandboxed environments, strict validation, allowlists, and/or removal of templating when not needed.

## Decision Table
| Situation | Action |
|-----------|--------|
| Code passes user-controlled strings directly into a template constructor (e.g., `Template(user_input)` or `env.from_string(user_input)`) | Remove dynamic templating: treat input as plain data, or validate with strict allowlist and render as literal text instead of executing as a template |
| Application uses a general-purpose template environment with many globals/filters exposed and autoescaping/undefined checks disabled | Introduce a restricted or sandboxed environment: enable autoescape, use `StrictUndefined`, clear default globals/filters, and only allow a minimal safe set |
| Code must support dynamic templates (e.g., admin-configurable templates) and already uses a supported engine (e.g., Jinja2) | Add a validation/compilation step (parse/compile API) before rendering, fail closed on errors, and ensure rendering uses the validated/sandboxed environment only |
| Rendering logic is duplicated across the app, each place constructing templates or environments ad hoc | Centralize into a single rendering module/service that exposes only template identifiers and strongly-typed data, never raw template source from callers |
| Input fields are later interpolated into templates but have no server-side validation | Add strict server-side validation and per-field allowlists that exclude template control characters (`{`, `}`, `%`) and limit length/format before passing to templates |

## Boundaries

### Can Do
- Identify obvious SSTI sinks such as `Template(user_input)` or `env.from_string(untrusted_str)` and rewrite them to non-templating or safe templating patterns.
- Introduce and configure safe/sandboxed template environments (e.g., Jinja2 `SandboxedEnvironment`, `StrictUndefined`, cleared globals/filters, blocked dunder access).
- Add server-side validation and allowlist-based checks on inputs that eventually reach templates, including regex-based enforcement and rejection of template delimiters.
- Centralize rendering behind a small, controlled API that only accepts known template names and validated data structures.
- Replace "smart" templating with literal output when the app does not need template logic at all.

### Cannot Do
- Guarantee safety for every possible template engine or framework without project-specific knowledge (custom template languages, proprietary engines may need human review).
- Decide business-acceptable input formats or user experience tradeoffs (e.g., how strict allowlists should be, what characters users must be allowed to enter).
- Re-architect template-heavy applications that deeply rely on runtime expression evaluation or metaprogramming; human design input is needed.
- Provide full runtime isolation (containers, separate processes, OS-level sandboxing); can only recommend and show how to plug code into such environments.
- Detect SSTI solely from comments, obfuscated code, or dynamic constructs that are not visible in static source.

## Gotchas
- Assuming client-side validation is enough: Relying on JavaScript or HTML constraints alone leaves the template engine exposed; all critical checks must run server-side before templating.
- Over-sanitizing instead of validating: Blindly stripping `{`/`}` or template delimiters from all inputs can break legitimate data and hide issues; prefer strict allowlists plus explicit rejection, only sanitizing in well-documented, narrow cases.
- Leaving default globals/filters intact: Using a sandbox or environment but forgetting to clear/limit globals and filters can still permit dangerous access paths (e.g., `__mro__`, filesystem helpers, or reflection via exposed functions).

## Quick Verification
```bash
# Run vulnerable example and show exploitation
python app_vulnerable.py "Hello {{ 7 * 7 }}"
# Expect: outputs "Hello 49" (evidence of SSTI)

python app_vulnerable.py "{{ ''.__class__.__mro__[1].__subclasses__() }}"
# Expect: stack trace / sensitive internal objects (dangerous)

# Run fixed example that removed templating and added allowlist
python app_fixed.py "Hello {{ 7 * 7 }}"
# Expect: ValueError about disallowed characters (SSTI blocked)

# Smoke-test a safe input path
python app_fixed.py "Hello, world!"
# Expect: "Hello, world!"

# Optional: for safe Jinja2 env, run unit tests
pytest -q  # assuming tests cover SSTI payloads like "{{ ''.__class__.__mro__ }}"
```