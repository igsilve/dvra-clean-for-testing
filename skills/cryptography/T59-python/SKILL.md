---
name: use-standard-libraries-for-cryptography
description: Use vetted standard cryptography APIs instead of custom or weak crypto code. Use when application code implements encryption, hashing, MACs, signatures, padding, or randomness directly, or uses insecure algorithms and practices.
---

# Use standard libraries for cryptography

## What This Skill Does
This skill replaces custom or weak cryptographic code with vetted standard library APIs. Apply it when code performs encryption, hashing, MACs, signatures, padding, key generation, nonce generation, or random-value generation manually, or when it uses insecure algorithms such as MD5 or handwritten XOR-based protection. The fix removes homemade crypto logic, switches to platform cryptography interfaces, uses secure randomness and generated keys, and prefers authenticated encryption so tampering is rejected.

## Decision Table
| Situation | Action |
|-----------|--------|
| Application code contains handwritten XOR, custom digest loops, manual padding, checksum logic, block processing, or signature math | Replace the custom implementation with standard cryptography APIs such as `Cipher`, `MessageDigest`, `Mac`, `Signature`, `KeyGenerator`, and `SecureRandom` |
| Code uses weak or inappropriate algorithms such as `MD5`, `SHA-1`, custom checksums for integrity, or non-cryptographic random sources for security decisions | Replace with a secure standard alternative appropriate to the purpose, such as `SHA-256`, `HmacSHA256`, `SecureRandom`, or authenticated encryption like `AES/GCM/NoPadding` |
| Code constructs keys, IVs, nonces, salts, or tokens manually or from predictable input | Generate them with standard key-generation and secure-random APIs |
| Code encrypts data without integrity protection or implements custom modes/padding | Replace with authenticated encryption through standard cipher APIs, preferably `AES/GCM/NoPadding` |
| Code already uses vetted standard cryptography APIs correctly and fails closed on verification errors | No action needed |

## Boundaries

### Can Do
- Replace homemade crypto routines with standard Java cryptography APIs
- Swap weak algorithms and insecure random generation for stronger standard choices
- Update code to use generated keys, secure nonces, and authenticated encryption patterns

### Cannot Do
- Choose business-specific cryptographic designs or protocol formats without requirements
- Safely invent a custom algorithm, mode, padding scheme, or key derivation approach
- Guarantee compatibility with existing stored hashes, ciphertexts, or external integrations without migration planning

## Gotchas
- Replacing custom encryption with plain hashing: hashing is not a drop-in replacement for encryption and cannot decrypt data later
- Using `java.util.Random` or predictable values for tokens, IVs, salts, or nonces: these are not cryptographically secure and can make secrets guessable
- Switching algorithms without checking purpose: `SHA-256` is fine for general hashing, but password storage usually needs a dedicated password-hashing function rather than a plain digest

## Quick Verification
```bash
# Find obvious weak or custom crypto patterns in Java code
grep -RInE 'MessageDigest\.getInstance\("MD5"|MessageDigest\.getInstance\("SHA-1"|new Random\(|SecureRandom|Cipher\.getInstance|Mac\.getInstance|Signature\.getInstance|[\^]\s*key|checksum|padding' .

# Confirm custom crypto helpers are removed or reduced
grep -RInE 'encrypt|decrypt|hash|digest|mac|signature|nonce|iv|salt|random' src/

# Build and run tests
mvn test

# If Gradle is used instead
./gradlew test
```