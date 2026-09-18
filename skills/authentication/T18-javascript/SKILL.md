---
name: make-authorization-decisions-using-full-context
description: Use when JavaScript authorization checks or downstream service calls make access decisions with only partial identity data, missing permissions/scope, or untrusted propagated claims.
---
# Make authorization decisions using full context

## What This Skill Does
This skill fixes insufficient authorization checks caused by missing end-user context. It updates JavaScript code so business logic and downstream services receive an explicit `authContext` object with the minimum required authorization attributes such as `userId`, `permissions`, `roles`, `tenantId`, and ownership scope. It also standardizes fail-closed behavior when context is missing, malformed, expired, incomplete, or untrusted, and ensures propagated claims are verified before use.

## Decision Table
| Situation | Action |
|-----------|--------|
| Authorization functions accept only `userId`, `documentId`, `action`, or similar partial inputs | Refactor the function to accept a canonical `authContext` object and make the decision from that full context plus resource attributes |
| Business/model/service-layer code re-fetches permissions or infers them from global/request state | Pass normalized permission and scope data directly into the method instead of re-fetching or inferring it |
| Downstream authorization relies on JWT or forwarded claims | Verify claims with `jwt.verify(...)`, validate required fields, audience, and freshness, then map only trusted claims into `authContext` |
| Client-supplied headers/body fields are used directly for authorization | Reject untrusted raw fields and authorize only from validated server-side or integrity-protected context |
| Code already passes normalized context and denies when required fields are missing | No action needed |

## Boundaries

### Can Do
- Refactor JavaScript authorization helpers and business methods to accept an explicit `authContext`
- Add normalization and fail-closed validation for required authorization fields
- Verify propagated JWT claims before downstream authorization decisions

### Cannot Do
- Invent the correct authorization policy when required permissions, roles, or scopes are undefined by the application
- Guarantee end-to-end trust across services without real signing keys, issuer rules, and deployment configuration
- Fix unrelated authentication flaws such as weak login, session handling, or broken identity proofing

## Gotchas
- Passing only `userId` as "context": this is still incomplete if the decision also depends on permissions, tenant, roles, ownership, or request scope
- Normalizing missing permissions to an empty array and then treating that as sufficient context: missing required claims should deny authorization, not silently downgrade checks
- Trusting decoded but unverified JWT data with `jwt.decode(...)`: decoded claims are not integrity-checked and must not drive authorization

## Quick Verification
```bash
# Confirm a canonical authorization context or verifier exists
rg -n "function\s+(normalizeAuthContext|authorizeDocumentAccess|verifyDownstreamAuthContext)\b|jwt\.verify\(" .

# Find likely unguarded or partial authorization patterns that bypass full-context checks
rg -n "function\s+\w*authoriz\w*\([^)]*(action|documentId|userId)[^)]*\)|\b(authoriz\w*|readDocument|canDeletePost)\([^,)]*(documentId|userId|action)[^)]*\)|jwt\.decode\(" .

# Build + test using the project's available JavaScript toolchain
npm test || yarn test || pnpm test || bun test
```