---
name: implement-account-lockout-or-authentication-throttling-for-system-accounts
description: Use when Python code authenticates system accounts without per-user failure tracking, lockout, or retry throttling, to prevent brute-force attacks.
---

# Implement account lockout or authentication throttling for system accounts

## What This Skill Does
This skill hardens Python authentication flows for system accounts that currently allow unlimited repeated password guesses. It adds per-user failure tracking and enforces either lockout, fixed-delay throttling, or exponential backoff before authentication can continue. The fix should run in application code on the authentication path, use configurable thresholds or delays, check throttle or lockout state before completing authentication, and reset state after successful authentication when that matches the intended policy. Use a monotonic time source such as `time.monotonic()` for elapsed lockout or retry timing.

## Decision Table
| Situation | Action |
|-----------|--------|
| `authenticate`, `login`, or similar code verifies system account credentials with `hmac.compare_digest(...)` and has no per-user failure state | Apply lockout or throttling in the authentication path before returning success/failure |
| Code already tracks `failed_attempts`, `lockout_until`, `throttle_until`, or `next_allowed_at` per username using `time.monotonic()` | No action needed unless checks happen after credential verification or state is never enforced |
| Code uses wall-clock time such as `time.time()` for retry windows | Replace elapsed-time comparisons with `time.monotonic()` for lockout/throttle timing |
| Repeated failures should become increasingly expensive but not permanently block access | Implement exponential backoff with configurable base delay and maximum delay |
| Successful authentication should clear retry penalties under the chosen policy | Reset per-user failure count and lockout/backoff timing on success |

## Boundaries

### Can Do
- Add per-user failed-attempt tracking for system account authentication in Python code
- Enforce configurable lockout, fixed throttling, or exponential backoff before authentication completes
- Replace wall-clock retry timing with `time.monotonic()` and reset state after success when policy requires it

### Cannot Do
- Choose the correct operational policy for every environment; teams must decide lockout thresholds and delay values
- Provide distributed persistence or cross-process synchronization by itself when authentication state must be shared across workers or hosts
- Prevent brute force against accounts authenticated outside the modified code path or by external identity providers

## Gotchas
- Using `time.time()` for retry windows: wall-clock changes can shorten or extend lockouts unexpectedly; use `time.monotonic()` for elapsed timing
- Checking credentials before lockout or throttle state: this still performs password verification on blocked attempts and weakens the control
- Tracking one global counter instead of per-user state: this can throttle unrelated users and does not correctly defend a single targeted account

## Quick Verification
```bash
# Confirm a guard exists for per-user lockout/throttle state and monotonic timing
rg -n -P "(failed_attempts|lockout_until|throttle_until|next_allowed_at)|time\.monotonic\(" .

# Find likely unguarded authentication code that still compares password hashes directly
rg -n -P "hmac\.compare_digest\s*\(" . | rg -v "(failed_attempts|lockout_until|throttle_until|next_allowed_at|_is_throttled|_record_failed_attempt|time\.monotonic)"

# Build/test using common Python toolchains; run what exists
python -m compileall .
pytest -q || python -m unittest discover -v
```