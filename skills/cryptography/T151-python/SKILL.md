---
name: use-cryptographically-secure-random-numbers
description: Fixes use of insufficiently random values by switching to cryptographically secure randomness, proper key/IV generation, and strong KDFs; use when tokens, keys, or secrets are generated with weak PRNGs or inadequate entropy
---

# Use cryptographically secure random numbers

## What This Skill Does
Detects and replaces insecure randomness in security-sensitive code (tokens, session IDs, keys, IVs, nonces, passphrase-derived keys). It guides replacing non-cryptographic PRNGs, time/counter patterns, or weak KDF usage with cryptographically secure random sources, correct key/IV sizes, sufficient entropy from user inputs, and KDFs with adequate work factors.

## Decision Table
| Situation | Action |
|-----------|--------|
| Security-sensitive value (token, reset code, session ID, API key, nonce, IV, CSRF token) is generated with `random`, `Math.random`, `java.util.Random`, linear counters, timestamps, or fixed seeds | Replace generator with a cryptographically secure RNG (e.g., `secrets`, `os.urandom`, `crypto.randomBytes`, `SecureRandom`) and remove seeding based on user or predictable data |
| Cryptographic keys, IVs, or nonces are derived from timestamps, counters, user IDs, or truncated hashes instead of CSPRNG bytes | Encapsulate key/IV/nonce creation in helpers that draw from a CSPRNG with explicit length constants matching algorithm requirements |
| User-supplied keys or structured secrets (e.g., hex keys in config/UI) are accepted without strict format/length validation | Enforce exact length and character set (e.g., 32 hex chars for AES-128); reject any deviation, whitespace, or normalization-required inputs |
| Passphrases are converted to keys with raw hashing (e.g., `sha256(password)`) or a KDF with very low iterations/work factor | Introduce a centralized KDF helper using PBKDF2/bcrypt/Argon2 with a stored work factor ≥ 10,000 iterations (or equivalent) and unique random salts |
| Code already uses a well-established CSPRNG (e.g., `secrets`, `crypto.randomBytes`, `SecureRandom` with default settings) and KDFs with adequate parameters and strict input validation | No action needed; only consider adding central utilities and tests if not already present |

## Boundaries

### Can Do
- Identify obvious insecure randomness in security-sensitive paths and convert it to standard cryptographically secure APIs.
- Introduce or refactor helper utilities for secure token/key/IV generation with explicit size constants.
- Add or tighten validation for user-provided keys/secrets and configure KDFs with reasonable minimum work factors and unique salts.

### Cannot Do
- Select project-specific cryptographic algorithms or key sizes where requirements or compliance rules are unknown.
- Guarantee global uniqueness of tokens across distributed systems beyond what proper CSPRNG and length provide.
- Precisely tune KDF parameters for performance/latency budgets without real runtime benchmarks.

## Gotchas
- Mixing secure and insecure randomness: Calling a CSPRNG once but then building the token with `random`/`Math.random` or counters still leaves predictability; all security-relevant bits must come from the CSPRNG.
- Reusing IVs/nonces: Even with CSPRNGs, caching or reusing the same IV/nonce for multiple encryptions in modes like GCM or CTR can break confidentiality and integrity.
- Weak "entropy" from user input: Treating long but low-entropy passphrases as direct keys or running them through a single hash (without a proper KDF and work factor) remains vulnerable to offline bruteforce.

## Quick Verification
```bash
# 1) Run vulnerable example and observe deterministic / predictable pattern
python app_vulnerable.py alice
python app_vulnerable.py alice   # Often same or easily guessable code pattern

# 2) Run fixed example and confirm codes appear unpredictable across runs
python app_fixed.py alice
python app_fixed.py alice

# 3) Sanity-check distribution and lack of bias (basic heuristic)
python - << 'PY'
import collections, secrets
N = 100000
digits = ''.join(str(secrets.randbelow(10)) for _ in range(N))
cnt = collections.Counter(digits)
print(cnt)
print("Min freq:", min(cnt.values()), "Max freq:", max(cnt.values()))
PY

# 4) Verify key/IV lengths in secure helpers (adapt names as needed)
python - << 'PY'
import secrets
AES_256_KEY_LEN = 32
AES_GCM_IV_LEN = 12
key = secrets.token_bytes(AES_256_KEY_LEN)
iv = secrets.token_bytes(AES_GCM_IV_LEN)
print(len(key) == AES_256_KEY_LEN, len(iv) == AES_GCM_IV_LEN)
PY

# 5) Verify KDF work factor and salt behavior (if using PBKDF2-style code)
python - << 'PY'
import hashlib, os
PBKDF2_ITERATIONS = 100_000
pw = "example-passphrase"
salt1 = os.urandom(16)
salt2 = os.urandom(16)
k1 = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt1, PBKDF2_ITERATIONS, dklen=32)
k2 = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt2, PBKDF2_ITERATIONS, dklen=32)
print("Iterations >= 10000:", PBKDF2_ITERATIONS >= 10_000)
print("Different salts -> different keys:", k1 != k2)
PY
```

---

## Additional Requirements (SD Elements project)

These requirements apply to T151 in this project because of its survey answers. Copied verbatim from SD Elements.

### ASVS Requirements - GUID v4 algorithm

Use a GUID v4 algorithm and a cryptographically-secure pseudo-random number generator (CSPRNG) to generate random globally unique identifiers (GUIDs), also known as universally unique identifiers (UUIDs). 

Since the GUID v4 is not cryptographically secure, it is recommended to use a CSPRNG to achieve both uniqueness and cryptographically secure pseudo-randomness. CSPRNGs are designed to meet the strict requirements for security and randomness, including unpredictability, resistance to tampering, and non-repeatability.

##References
[Recommendation for Random Number Generation Using Deterministic Random Bit Generators](https://csrc.nist.gov/publications/detail/sp/800-90a/rev-1/final)
