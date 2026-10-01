---
name: perform-message-throttling
description: Message throttling and basic rate limiting for Web APIs to mitigate DoS; Use when endpoints expose expensive or sensitive operations without per-identity request limits or backoff.
---

# Perform message throttling in Web APIs

## What This Skill Does
Implements per-identity throttling in Web API handlers so that a single IP, user, or API key cannot send unlimited high-frequency requests. It adds rolling time-window checks and lock/delay responses (e.g., HTTP 429) around expensive or sensitive operations to reduce Denial of Service (DoS) and brute-force risk.

## Decision Table
| Situation | Action |
|-----------|--------|
| Endpoint exposes CPU/IO‑heavy work that can be called repeatedly (e.g., `/compute` with large loops) and there is no per‑client limit | Add per‑identity rolling‑window throttling before the expensive operation and return HTTP 429 when over limit |
| Authentication, password reset, or other sensitive action is callable unlimited times from same IP/API key | Add separate rate limits for failed attempts and overall requests per identity; enforce lockout or backoff when thresholds exceeded |
| Service already uses a centralized API gateway / WAF with clearly configured per‑identity rate limits covering this route | No additional application‑level throttling required unless business logic needs stricter limits |
| In‑app throttling is implemented but uses only a global counter (no per‑identity tracking) | Replace with per‑identity tracking keyed by IP/API key/user ID; prune timestamps outside the configured window |
| Throttling logic exists but does not prune old timestamps or never resets lock state | Fix logic to discard events older than the window and to correctly expire locks or require explicit admin reset, per policy |

## Boundaries

### Can Do
- Add simple, in‑process throttling around web handlers (e.g., Flask/Django/FastAPI controllers) using per‑identity rolling windows.
- Recommend and implement lockout or backoff policies (HTTP 429, fixed lock window, or increasing delay).
- Limit brute‑force and resource‑exhaustion attempts from a single identity (IP, API key, user ID).

### Cannot Do
- Cannot replace infrastructure‑level protections (WAF, API gateway, CDN) for very high‑traffic or distributed DoS attacks.
- Cannot reliably identify real users behind NAT/proxies when only IP is available; identity quality depends on existing headers/auth.
- Cannot make in‑memory throttling state durable or shared across multiple processes/servers without using external storage (Redis, DB).

## Gotchas
- Using only IP as identity in shared environments: Can throttle multiple legitimate users behind the same IP; prefer API key/user ID where available.
- Forgetting to prune old timestamps from the tracking window: Causes permanent or growing throttling even when traffic returns to normal, and can increase memory usage.
- Relying solely on request payload size limits: Caps immediate workload but does not stop rapid repeated calls; message throttling still needed.

## Quick Verification
```bash
# 1. Run the Flask app (example)
export FLASK_APP=app_fixed.py
flask run --port 5000

# 2. Send multiple requests within the window from the same client
for i in {1..7}; do
  curl -s "http://127.0.0.1:5000/compute?n=100" -o /dev/null -w "Req $i -> %{http_code}\n"
done
# Expect first ~5 requests to be 200 and subsequent ones to be 429 within 60 seconds

# 3. Wait for the window to pass, then try again
sleep 65
curl -s "http://127.0.0.1:5000/compute?n=100" -o /dev/null -w "After window -> %{http_code}\n"
# Expect 200 (throttling window reset)

# 4. CLI path throttling (if main() wired as in example)
python app_fixed.py 100
python app_fixed.py 100
python app_fixed.py 100
# After exceeding configured limit in a short time, expect a stderr message:
# "Too many requests from CLI; throttled."
```

---

## Additional Requirements (SD Elements project)

These requirements apply to T1362 in this project because of its survey answers. Copied verbatim from SD Elements.

### Web API - throttling types

You can apply different types of throttling as follows:

- __Rate-limit throttling__: A simple throttle limits the number of requests passing through during a time interval. A throttle can be based on the number of requests, size of a payload, or content.

- __IP-level throttling__: Make your API accessible only to white-listed IP addresses, or limit the number of requests sent by a specific client IP.

- __Scope-limit throttling__: Restrict access to specific parts of the API, such as certain methods, functions, or procedures that are based on the users' roles. You can take advantage of the same API across your organization by Implementing scope limiting.

- __Concurrent connections limit__: Limit the number of connections from a user/account to avoid a Denial of Service error when your application cannot respond to more than a certain number of connections.

- __Resource-level throttling__: Use resource-level throttling or hard throttling to limit the number of returned records from your API.
For instance, if a certain query returns a large number of records, throttle the request so that your SQL engine limits the number of rows returned by using conditions attributes such as TOP, SKIP, SQL_ATTR_MAX_ROWS, and so on.

- __Tiers of throttling__: Apply throttling at multiple levels in your organization:
    - API-level throttling
    - Application-level throttling
    - User-level throttling
    - Account-level throttling

## References
[How to Rate-Limit an API Query](https://www.progress.com/blogs/how-to-rate-limit-an-api-query-throttling-made-easy)

### Secure API Resource Consumption Guidelines

- Use a solution that makes it easy to limit memory, CPU, number of restarts, file descriptors, and processes, such as Containers / Serverless code (e.g. Lambdas).

- Define and enforce a maximum size of data on all incoming parameters and payloads, such as maximum length for strings, maximum number of elements in arrays, and maximum upload file size (regardless of whether it is stored locally or in cloud storage). Reject requests that require excessive work. Look for work that scales nonlinearly, which means it suddenly requires exponentially more time to complete when you pass a certain threshold. Thorough testing can help you detect issues that you might not catch in a code review.


- Implement a limit on how often a client can interact with the API within a defined timeframe (rate limiting).

- Rate limiting should be fine-tuned based on the business needs. Some API Endpoints might require stricter policies.

- Limit/throttle how many times or how often a single API client/user can execute a single operation (for example, validate an OTP, or request password recovery without visiting the one-time URL).

- Add proper server-side validation for query strings and request body parameters, specifically the one that controls the number of records to be returned in the response.

- Configure spending limits for all service providers/API integrations. When setting spending limits is not possible, billing alerts should be configured instead.
- Deploy techniques that can slow down automated access to sensitive business operations (for example, making and receiving payment, authentication, core business use case and so on) such as device fingerprinting, human detection, non-human pattern analysis, blocking known threat sources and so on.
