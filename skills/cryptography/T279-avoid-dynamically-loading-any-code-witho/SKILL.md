---
name: t279-avoid-dynamically-loading-any-code-witho
description: Avoid dynamically loading any code without proper security considerations
---

# T279: Avoid dynamically loading any code without proper security considerations

**Category:** IN
**SD Elements:** [T279](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/development/4552-T279/)
**Priority:** 8

### Task T279: Avoid dynamically loading any code without proper security considerations (DOCUMENTATION ONLY)

**Guidance:** While dynamic loading of code is possible in some programming languages and frameworks like Java and Android, it is recommended that you avoid this capability as it increases the code complexity and makes your application dependent on an external resource. However, If you have to load any module dynamically, consider the following recommendations:

- Avoid loading modules from shared locations, such as from an external storage.

- Avoid loading modules through unencrypted networks. Otherwise, files in transit would be at risk of manipulation.

- If you have to load a class from an external location, generate a signature of the class (binary) and check the signature before loading the class to verify that the integrity of the class is maintained.

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Documented
