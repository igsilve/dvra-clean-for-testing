---
name: use-jwt-securely
description: Use secure JWT/JWE verification and issuance patterns in Python; use when code signs, parses, verifies, or decrypts JSON Web Tokens and may trust attacker-controlled headers, weak keys, or disabled verification.
---

# Use JSON Web Token (JWT) securely

## What This Skill Does
This skill fixes insecure JWT handling in Python by replacing unsafe decode/verification patterns with centralized JOSE library usage that pins allowed algorithms, verifies signatures or MACs, validates required claims, uses trusted server-side key lookup for `kid`, rejects `alg: none`, and uses JWE when token contents must be confidential. Apply it when code uses PyJWT or JOSE libraries to issue, parse, verify, or decrypt tokens, or when code manually handles JWT structure or crypto.

## Decision Table
| Situation | Action |
|-----------|--------|
| `jwt.decode(..., options={"verify_signature": False})`, `verify=False`, or acceptance of `"none"` is found | Replace with explicit `jwt.decode(token, key, algorithms=[...])` and fail closed on verification errors |
| JWT verification trusts `alg`, `kid`, or other JOSE header values to choose behavior | Bind algorithm and key lookup in trusted server-side code; allowlist expected `alg`, validate `typ`, and reject unknown `kid` |
| Code verifies tokens but does not require or validate `exp`, `iat`, `nbf`, `iss`, `aud`, or `sub` as needed | Add claim validation and `options={"require": [...]}` for required claims |
| Sensitive claims are stored in signed-only JWTs | Replace with JWE using a standard JOSE library and authenticated encryption such as `jwe.encrypt(..., algorithm="dir", encryption="A256GCM")` |
| Code already uses standard JOSE libraries with explicit algorithms, trusted keys, and claim validation | No action needed |

## Boundaries

### Can Do
- Replace insecure PyJWT decode patterns with explicit signature verification and algorithm allowlists
- Centralize JWT validation, including trusted `kid` lookup and required claim checks
- Flag places where JWE is needed because token contents must remain confidential

### Cannot Do
- Choose correct issuer, audience, subject, or token lifetime rules without application context
- Invent or rotate production keys, JWKS contents, or external identity-provider configuration
- Guarantee interoperability for custom token formats or non-standard JOSE behavior

## Gotchas
- Checking the header but not enforcing it in `jwt.decode`: header inspection alone is not verification; the allowed algorithm must also be pinned in trusted code
- Accepting `kid` directly from the token without a trusted lookup: attackers can select unexpected keys or bypass intended verification paths
- Using signed-only JWTs for secrets or personal data: JWS protects integrity, not confidentiality; use JWE for sensitive claims

## Quick Verification
```bash
# Confirm secure verification wrappers or allowlisted decode paths exist
rg -n 'jwt\.decode\([^)]*algorithms=\[[^]]+\]|get_unverified_header\(|options=\{"require": \[|jwe\.(encrypt|decrypt)\(' .

# Find unguarded dangerous JWT API usage and custom-bypass patterns
rg -n 'jwt\.decode\([^)]*(verify=False|verify_signature"\s*:\s*False|algorithms=\[[^]]*"none"|options=\{"verify_signature":\s*False)|jwt\.decode\(\s*[^,)]*\s*\)|get_unverified_header\([^)]*\)(?![\s\S]{0,200}alg)|base64\.urlsafe_b64decode|hmac\.new\(' .

# Build + test using the Python toolchain
python -m compileall .
python -m unittest discover
```