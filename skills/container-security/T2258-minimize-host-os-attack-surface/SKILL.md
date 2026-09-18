---
name: t2258-minimize-host-os-attack-surface
description: Minimize host OS attack surface
---

# T2258: Minimize host OS attack surface

**Category:** IN
**SD Elements:** [T2258](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T2258/)
**Priority:** 7

### Task T2258: Minimize host OS attack surface (DOCUMENTATION ONLY)

**Guidance:** Follow the steps below to reduce the host OS attack surface:

- Use a container-specific OS as opposed to a general purpose operating system wherever possible.
- Harden hosts and keep them up-to-date.
- Do not run other apps, like a web server or database, on hosts that run containers.
- Do not run unnecessary system services on hosts that run containers.
- Maintain a schedule to continuously scan hosts and the appropriate lower-level components for vulnerabilities and updates, such as with the kernel. 

For organizations that cannot use a container-specific OS, see NIST's [Guide to General Server Security](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-123.pdf).

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Documented
