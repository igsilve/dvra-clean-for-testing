---
name: t2605-validate-database-traffic
description: Validate database traffic
---

# T2605: Validate database traffic

**Category:** IN
**SD Elements:** [T2605](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T2605/)
**Priority:** 9

### Task T2605: Validate database traffic (DOCUMENTATION ONLY)

**Guidance:** To protect against protocol vulnerabilities:

- Parse and validate all database traffic to make sure it's well-formed and is what you're expecting. Block anything that doesn't match what should be coming. This way, you can mitigate the effects of forged packets and other attacks.
- Configure your network and servers to use more secure variants of protocols, such as IPsec instead of IP, DNSsec instead of DNS, and SBGP instead of BGP.


Use multiple firewalls:

- One way to help protect your databases is to separate your development, testing, and production databases, is to host them on separate servers, each firewalled from the other. If this is not possible you should, at minimum, separate testing and development from production via an internal firewall. This is a different firewall from the one screening incoming requests from the Internet to the production server.

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Documented
