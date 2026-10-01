---
name: generate-unique-session-ids-and-reset-old-ids-after-authentication
description: Use when Python code accepts or reuses client-supplied session IDs across login or privilege changes; enforce server-generated session IDs and rotate them after authentication to prevent session fixation.
---
# Generate unique session IDs and reset old IDs after authentication

## What This Skill Does
This skill fixes session fixation in Python by ensuring the application only accepts session IDs that the server created, generates session IDs from a cryptographically secure random source, regenerates the session ID after successful authentication or privilege elevation, copies only required server-side session state to the new session, and invalidates the old session ID immediately so attacker-chosen or stale IDs cannot remain bound to an authenticated session.

## Decision Table
| Situation | Action |
|-----------|--------|
| Incoming cookie, header, query, or CLI value is used as a session ID and trusted directly | Replace with a lookup that accepts the ID only if it already exists in the server-side session store; otherwise create a new server-generated session ID |
| Login or privilege-change flow keeps the same session ID after success | Apply session ID regeneration immediately after authentication or privilege elevation, copy required server-side state, and delete the old session ID |
| Session IDs are generated with weak or ad hoc randomness | Replace with `secrets.token_urlsafe(...)` or `secrets.token_hex(...)` with enough entropy |
| Session state is stored server-side and mapped by server-created IDs | Keep that design and ensure unknown incoming IDs are rejected rather than adopted |
| Code already validates incoming IDs against a server-side store and rotates IDs on auth changes | No action needed |

## Boundaries

### Can Do
- Replace direct reuse of client-controlled session IDs with server-generated IDs
- Add a regeneration function that copies required session state and invalidates the old ID
- Update authentication and privilege-change flows to rotate the session ID after success

### Cannot Do
- Redesign a full authentication architecture beyond session fixation mitigation
- Guarantee framework-specific session middleware is configured correctly without inspecting that framework
- Fix unrelated session issues such as missing cookie flags, CSRF protection, or weak logout behavior unless explicitly requested

## Gotchas
- Regenerating the ID but keeping the old session entry valid: this still allows fixation because the attacker-known ID can continue to resolve
- Copying all old session data blindly: this can preserve stale privilege or inconsistent state; copy only required server-side fields
- Accepting any supplied session ID and creating state under it: this defeats the fix because the application is still honoring attacker-controlled identifiers

## Quick Verification
```bash
# Confirm secure generation and regeneration helpers exist
rg -n "secrets\.(token_urlsafe|token_hex)\(" .
rg -n "def (_?regenerate_session_id|regenerate_session_id)\(" .

# Find unguarded dangerous patterns: direct trust of external session IDs or auth bound to an existing ID without rotation
rg -n "request\.(cookies|get_json|args|headers)\.get\(['\"]session(_id)?['\"]\)|sys\.argv\[|external_session_id" .
rg -n "_fake_sessions\[[A-Za-z_][A-Za-z0-9_]*\]\[['\"]authenticated['\"]\]\s*=\s*True" .
rg -n "return\s+(session_id|sid)\b" .

# Build/test using generic Python toolchain commands
python -m compileall .
python -m unittest discover -v
pytest -q
```

---

## Additional Requirements (SD Elements project)

These requirements apply to T20 in this project because of its survey answers. Copied verbatim from SD Elements.

### MDS2 Notes

The following MDS2-2013 question(s) relate to this task:

__3-1.__ Can the device prevent access to unauthorized users through user login requirements or other mechanisms?
