---
name: t2349-configure-software-to-have-secure-settin
description: Configure software to have secure settings by default
---

# T2349: Configure software to have secure settings by default

**Category:** IN
**SD Elements:** [T2349](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T2349/)
**Priority:** 8

### Task T2349: Configure software to have secure settings by default (DOCUMENTATION ONLY)

**Guidance:** Define and implement secure default settings for the software baseline by determining how to configure each setting that has an effect on security so that the default settings are secure and do not weaken the security functions provided by the platform, network infrastructure, or services.

- Conduct testing to ensure that the settings, including the default settings, are working as expected and are not inadvertently causing any security weaknesses, operational issues, or other problems.
- Verify that the approved configuration is in place for the software.
- Document each setting's purpose, options, default value, security relevance, potential operational impact, and relationships with other settings.
- Use authoritative programmatic technical mechanisms to document how each setting can be implemented and assessed by software administrators.
- Store the default configuration in a usable format and follow change control practices for modifying it (e.g., configuration as code).

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Applied
