---
name: t4747-limit-container-privileges
description: Limit container privileges
---

# T4747: Limit container privileges

**Category:** IN
**SD Elements:** [T4747](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T4747/)
**Priority:** 10

### Task T4747: Limit container privileges (DOCUMENTATION ONLY)

**Guidance:** The purpose of implementing the principle of least privilege (PoLP) for containers is to minimize the risk of exploitation by ensuring that containers only have the minimum privileges necessary to perform their functions. This reduces the potential damage if a container is compromised. 

1. Avoid running containers as root unless absolutely necessary. Running containers as root can expose the system to significant security risks if the container is compromised.
2. Use user namespaces to isolate the privileges of containers. This helps in mapping container user IDs to different host user IDs, providing an additional layer of security.
3. Implement security contexts to control the access and capabilities of containers. Security contexts allow you to define the security settings for a pod or container, such as setting the user ID, group ID, and capabilities.

After implementing this countermeasure, a secure system will have containers running with only the necessary privileges, reducing the risk of privilege escalation and limiting the impact of any potential security breaches.

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Applied
