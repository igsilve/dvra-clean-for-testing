---
name: t2620-protect-data-in-transit-with-tls-postgre
description: Protect data in transit with TLS (PostgreSQL)
---

# T2620: Protect data in transit with TLS (PostgreSQL)

**Category:** IN
**SD Elements:** [T2620](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T2620/)
**Priority:** 9

### Task T2620: Protect data in transit with TLS (PostgreSQL) (DOCUMENTATION ONLY)

**Guidance:** Verify that TLS is enabled for PostgreSQL by running this query:

	SELECT * FROM pg_stat_ssl;

If TLS is not enabled, all rows will be `null`, except `ssl`, which will be `f` (false).

Enabling TLS requires several steps, including creating certificates and setting the following properties in the __PostgreSQLql.conf__ file:
- `ssl = on`
- `ssl_min_protocol_version = 'TLSv1.3'` (to force clients to use TLS v1.3 or newer, as older versions are deprecated as insecure)
- `ssl_cert_file` and `ssl_key_file` to point to your server certificate and key file

A full walkthrough of TLS configuration instructions is available in the PostgreSQL documentation at https://www.PostgreSQLql.org/docs/current/ssl-tcp.html.

## Note
TLS is recommended to protect all connections, even over internal networks.

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Documented
