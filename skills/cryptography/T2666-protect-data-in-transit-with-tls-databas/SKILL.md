---
name: t2666-protect-data-in-transit-with-tls-databas
description: Protect data in transit with TLS (Database Server)
---

# T2666: Protect data in transit with TLS (Database Server)

**Category:** IN
**SD Elements:** [T2666](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T2666/)
**Priority:** 8

### Task T2666: Protect data in transit with TLS (Database Server) (DOCUMENTATION ONLY)

**Guidance:** Transport Layer Security (TLS, sometimes known as SSL), encrypts network communication between a client and the database. To ensure a secure deployment, follow these guidelines:
- TLS must be __required__ for all remote database connections (not just enabled).
- TLS connections should require a minimum version of TLS 1.2, as earlier versions have known weaknesses.
- It must not be possible to circumvent TLS by connecting with an alternate, less secure protocol.

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Documented
