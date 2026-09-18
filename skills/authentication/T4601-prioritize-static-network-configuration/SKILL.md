---
name: t4601-prioritize-static-network-configuration
description: Prioritize static network configuration
---

# T4601: Prioritize static network configuration

**Category:** IN
**SD Elements:** [T4601](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T4601/)
**Priority:** 8

### Task T4601: Prioritize static network configuration (DOCUMENTATION ONLY)

**Guidance:** - Configure hosts and devices to use static IP addresses and network settings, where feasible.

Although configuring hosts and devices to use static IP addresses and network settings is a security best practice that enhances network stability, prevents unauthorized DHCP attacks, improves network visibility and control, mitigates IP address spoofing risks, and reduces the risk of service disruptions, it is essential to evaluate its feasibility based on network architecture, device limitations, and operational requirements.

Considerations and Limitations
- Scalability: Managing static IPs in large networks can be complex and may require centralized IP management solutions.
- Operational Constraints: Some environments, such as cloud-based infrastructures or highly dynamic networks, may require DHCP for flexibility and automation.
- Hybrid Approach: In cases where static IPs are impractical, organizations should implement additional DHCP security measures (e.g., DHCP snooping, IP-MAC binding) to mitigate risks.

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Applied
