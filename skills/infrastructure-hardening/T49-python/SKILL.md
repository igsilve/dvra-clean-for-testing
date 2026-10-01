---
name: disable-and-remove-debug-capabilities-and-codeda
description: 'Secure coding guidance for weakness Active Debug Capabilities or Debug
  Code, or Unnecessary Files (P379). Use when implementing or reviewing: Disable and
  remove debug capabilities and code/data, and prepare application for release.'
---

# Disable and remove debug capabilities and code/data, and prepare application for release

## What This Skill Does
Removes or hardens active debug features, backdoors, and leftover development artifacts before release. It replaces unsafe debug helpers (like `eval`-based tools and hardcoded passwords), ensures production configurations never enable debug behavior accidentally, and strips unnecessary metadata or files that could leak information or expand attack surface.

## Decision Table
| Situation | Action |
|-----------|--------|
| Debug flags (`DEBUG_MODE`, `app.debug`, `FLASK_ENV`, `DEBUG=True`) are still used to gate powerful behavior in production paths | Disable these flags for production and ensure no sensitive/privileged behavior is reachable regardless of their value |
| Debug helper uses `eval`/`exec` or similar on user-controlled input | Replace with a constrained, non-executable parser/evaluator (e.g., restricted AST-based evaluator) or remove the capability entirely |
| Debug / “backdoor” login with hardcoded password or bypassed checks is present | Remove the backdoor. If tests require the function, make it a non-security helper (e.g., always fail or only simulate success in isolated test paths, not wired to real auth) |
| Web framework (e.g., Flask) is configured via environment (e.g., `FLASK_ENV`, `DEBUG`) and may enable debugger in production | Force production config to set `DEBUG=False`, disable interactive debugger, and never auto-enable debug based only on environment variables |
| Code contains rich annotations or debug-only metadata not needed at runtime | Strip or minimize annotations/metadata in production, ensuring they don’t contain secrets or internal details |
| Codebase already has no active debug routes, backdoors, or unsafe debug helpers and production config forces debug off | No action needed |

## Boundaries

### Can Do
- Identify and remove or neutralize unsafe debug helpers that execute arbitrary input (e.g., `eval`, `exec`, shelling out).
- Replace debug backdoors and hardcoded debug credentials with safe placeholders that are not used for real authentication.
- Enforce secure production configuration (e.g., Flask `create_app` that never enables debug in production, safe cookie flags).
- Gate optional debug endpoints behind explicit, non-production-only configuration flags that default to disabled.
- Strip non-essential annotations/metadata in production and ensure annotations do not contain secrets.

### Cannot Do
- Cannot guarantee that every debug hook in a large codebase is found; hidden or dynamically loaded debug code may remain.
- Cannot change business or QA requirements that rely on unsafe debug behavior without human agreement (e.g., tests that expect real backdoor access).
- Cannot retrofit full authentication/authorization; this skill can only neuter debug paths and simulate legacy behavior where necessary.
- Cannot manage or delete external debug artifacts (e.g., database dumps, logs, symbol files) outside the application code unless explicitly scripted.

## Gotchas
- Leaving debug helpers reachable: Simply setting `DEBUG_MODE = False` is not enough if there are any code paths (tests, CLI tools, routes) that still call dangerous debug functions. The functions themselves must be made safe or removed.
- Treating “debug login” as real auth: Keeping a “debug_backdoor_login`-style helper and wiring it into Flask routes or admin flows reintroduces the backdoor. Even if it returns `True` only in tests, it must not participate in real authentication.
- Relying on environment flags alone: Assuming `FLASK_ENV=production` or `DEBUG=0` is sufficient can be dangerous. The app should explicitly set `DEBUG=False` and never auto-enable debugging based solely on environment variables.
- Over-aggressive stripping: Blindly stripping annotations or metadata can break libraries that depend on them for behavior (e.g., frameworks using type hints for routing or validation). Restrict stripping to your own modules and benign annotations.

## Quick Verification
```bash
# 1. Static grep checks for obvious debug artifacts
grep -R --line-number -E 'eval\(|exec\(' .
grep -R --line-number -E 'DEBUG_MODE|DEBUG\s*=' .
grep -R --line-number -E 'let_me_in_debug|backdoor|hardcod(ed)?_password' .

# 2. Run the vulnerable vs fixed demo (Python)
python app_vulnerable_code.py "debug_eval:__import__('os').system('id')"  # SHOULD BE VULNERABLE (for demo only)
python app_fix_python_code.py "debug_eval:__import__('os').system('id')"   # SHOULD RETURN "Invalid expression"

python app_vulnerable_code.py "debug_login:let_me_in_debug"  # Returns OK (backdoor)
python app_fix_python_code.py "debug_login:let_me_in_debug"   # Returns OK only for legacy behavior, not wired to auth

# 3. Flask production behavior (no debug)
export FLASK_ENV=production
python -c "from app_fix_python_code import create_app; app = create_app(); print(app.debug, app.testing)"

# 4. Annotation stripping behavior
python -c "import app_fix_python_code as m; print(m.some_function.__annotations__); m.strip_annotations(); print(m.some_function.__annotations__)"
```

---

## Additional Requirements (SD Elements project)

These requirements apply to T49 in this project because of its survey answers. Copied verbatim from SD Elements.

### Deploy the product with a secure initial configuration

Deploy the product with a secure initial configuration.

Product Secure "Out of the Box" is the principle of deploying a secure initial configuration of the system. This is crucial to protecting the confidentiality, integrity, and availability of the system and its data. 
    - By default, apply all default settings that mitigations rely on within the product before first processing any sensitive data, upon installation, initialization, or first use of the software.                        
    -  Enable all product security controls, features, and functions upon installation, initialization, or first use

### Avoid information leak through HTTP headers

Avoid including unnecessary information such as detailed server version and name in HTTP headers or any part of the HTTP response.
