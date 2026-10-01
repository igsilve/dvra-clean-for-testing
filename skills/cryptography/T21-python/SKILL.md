---
name: encrypt-data-in-transit-tls
description: Ensure all sensitive data in transit uses a secure, modern TLS channel; use when fixing cleartext or weakly protected network communication (CWE-319 / P216).
---

# Ensure all data in transit is encrypted using a secure TLS channel

## What This Skill Does
This skill detects and replaces cleartext or weakly protected data-in-transit paths with secure, modern TLS usage. It helps enforce HTTPS/TLS for authentication and sensitive endpoints, harden TLS protocol and cipher settings, reject plaintext authentication, avoid protocol downgrades, and disable HTTP/TLS compression where secrets are present, reducing the risk of credential theft and traffic tampering.

## Decision Table
| Situation | Action |
|-----------|--------|
| Code sends credentials, tokens, or personal data over `http://`, raw `socket`/`net`/`socket.sendall` with no TLS | Replace with HTTPS/TLS client or wrap socket using a secure TLS context that enforces certificate validation |
| Server exposes login, token, or account endpoints over HTTP or accepts auth on non-secure requests | Enforce HTTPS-only for these routes and reject/redirect plaintext authentication attempts |
| TLS contexts or servers rely on default protocol versions (or allow SSLv3/TLS1.0/1.1) | Explicitly set minimum TLS version (e.g., TLS 1.2+) and restrict maximum to a modern version (e.g., TLS 1.3) |
| TLS configuration uses broad/legacy cipher lists or defaults with no ordering | Configure a curated modern cipher suite set, enable server cipher preference, and disable TLS compression |
| Dynamic responses include tokens/session IDs and are served with HTTP compression (gzip/br) | Disable HTTP compression (or skip compression middleware) for these responses and set headers to discourage intermediary compression |
| Code already uses HTTPS/TLS with modern versions, strong ciphers, cert validation, and no compression on secret-bearing responses | No action needed |

## Boundaries

### Can Do
- Identify and replace cleartext network calls (HTTP, raw sockets) carrying sensitive data with secure TLS-based equivalents.
- Configure TLS client/server contexts to enforce modern protocol versions, strong cipher suites, and disabled TLS-level compression.
- Add application-level checks to reject plaintext authentication and to avoid HTTP compression on secret-bearing responses.
- Use framework or language-standard libraries (e.g., Node.js `https`/`tls`, Python `ssl`) to apply these patterns consistently.

### Cannot Do
- Generate or manage real production certificates, private keys, or PKI infrastructure (can only reference paths or placeholders).
- Reconfigure external infrastructure (load balancers, CDNs, API gateways, service meshes) that is not represented in the codebase.
- Guarantee regulatory or compliance adherence (PCI, HIPAA, etc.); only improve technical transport security.
- Fix unrelated issues like password storage, authorization logic, or input validation (beyond transport concerns).

## Gotchas
- Assuming `https://` is enough: Failing to set `rejectUnauthorized` / certificate verification (or disabling it) leaves you open to MITM even over TLS.
- Leaving legacy protocols enabled: Not explicitly setting `minVersion` / `minimum_version` can allow SSLv3/TLS1.0/1.1 if platform defaults are weak.
- Compressing secrets: Keeping HTTP compression on for responses that include tokens, cookies, or other secrets can enable compression side-channel attacks.
- Trusting all proxy headers: Using `x-forwarded-proto` without restricting it to trusted proxies can let attackers spoof “https” and bypass plaintext-auth checks.

## Quick Verification
```bash
# 1) Confirm no cleartext credential paths
grep -RIn --exclude-dir=.git -E "http://|socket\.socket\(|net\.Socket\(" .

# 2) Scan TLS protocol and cipher support (replace host/port)
nmap --script ssl-enum-ciphers -p 443 your-app.example.com

# 3) Check that old TLS versions are rejected
openssl s_client -connect your-app.example.com:443 -tls1
openssl s_client -connect your-app.example.com:443 -tls1_1

# 4) Verify HTTPS-only auth (replace URL)
curl -v http://your-app.example.com/login -d 'u=a&p=b'
curl -v https://your-app.example.com/login -d 'u=a&p=b'

# 5) Verify no compression on secret-bearing responses
curl -v -H 'Accept-Encoding: gzip,br' https://your-app.example.com/secret-endpoint
```

---

## Additional Requirements (SD Elements project)

These requirements apply to T21 in this project because of its survey answers. Copied verbatim from SD Elements.

### Enforce TLS/SSL on all pages

Enforcing TLS/SSL (We use the word "TLS" to also refer to the secure versions of SSL after this) across your entire site limits the ability of phishers to pull off impersonation attacks on your application and provides a higher level of security to your users. However, whole-site TLS has some cons that should be considered:

- TLS requires more processing power and bandwidth and increases server overhead.
- Content Distribution Networks (CDN) may face challenges distributing your protected pages.
- Ad networks used by your application may not support TLS.

So, in minimum, use TLS for the parts of your site that need security such as login pages, authenticated pages, sensitive submission forms and other content that needs to be encrypted. And if the above-mentioned problems are not critical to you, force TLS on all pages to enable a higher level of security for your application.

__Note__: Even if part of the application does not particularly perform any sensitive actions or collect sensitive data, allowing non-TLS access to those parts causes non-secure cookies (the ones that don't have "secure" flag set to true on them, [see T22](/library/tasks/T22/)) to be sent over unencrypted channels. Those cookies can be stolen by any eavesdropper on the network. Other small problems in the application could also be exploited much more easily when the whole application is not TLS-enforced.

### Choice of cipher

## Choice of cipher

Use the following guidelines for selecting an appropriate cipher for encryption:

- Strictly avoid using NULL ciphers as they do not provide encryption for confidentiality (they only provide integrity checks).
- Strictly avoid using EXPORT ciphers (EXPORT ciphers use shorter keys and are weak and breakable by design). The server component must explicitly disable EXPORT ciphers to protect the clients against __Factoring RSA Export Keys__ (FREAK) attacks.
- Strictly avoid DES ciphers (not to be confused with 3DES). They have a short key and can be broken easily by brute force using inexpensive off-the-shelf hardware.
- Where available, use Ephemeral key exchange ciphers over standard ones. That is, use __ECDHE__ over ECDH and __DHE__ over DH.
- Regarding DH-based key changes, choose ECDH\* over DH\* due to better performance. ECDH\* provides the same amount of protection as DH\* but the former requires fewer resources.
- Never use ciphers that use MD5 for MAC.
    - MD5 has two known weaknesses: collision and pre-image.
- Never use SHA1. Use SHA384 or SHA256 instead.
    - SHA1 has been fully and practically broken.
    
Refer to [this page](https://ciphersuite.info/cs/?sort=asc&software=gnutls&singlepage=true&security=secure&tls=tls12) for a list of recommended ciphers.

### Secure files transfer

Do not transmit files in cleartext in a communication channel as it jeopardizes the integrity and confidentiality of data as unauthorized actors may sniff it. Use secure file transfer tools that:

1. Employ secure File Transfer protocols (e.g., Secure File Transfer Protocol (SFTP), FTP over SSL (FTPS), and Applicability Statement 2 (AS2)) that encrypt the data in motion and at rest. 
2. Use robust authentication methods.
3. Protect against unauthorized data modifications. 
4. Have reporting and logging capabilities.

### Connect to a remote system securely

- Connect securely to a remote system using the SSH (Secure Shell) protocol that encrypts the traffic between a client and a server, preventing interception and identity spoofing.
- Do not use Telnet to connect to a system remotely. Telnet sessions between a client and a server are not encrypted, exposing the connection to various threats, including eavesdropping and identity spoofing.
