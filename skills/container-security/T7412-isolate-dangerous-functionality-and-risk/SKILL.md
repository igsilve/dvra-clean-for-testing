---
name: t7412-isolate-dangerous-functionality-and-risk
description: Isolate dangerous functionality and risky third-party components using sandboxing or encapsulation
---

# T7412: Isolate dangerous functionality and risky third-party components using sandboxing or encapsulation

**Category:** IN
**SD Elements:** [T7412](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/development/4552-T7412/)
**Priority:** 9

### Task T7412: Isolate dangerous functionality and risky third-party components using sandboxing or encapsulation (DOCUMENTATION ONLY)

**Guidance:** Apply additional protective controls around application areas documented as containing dangerous functionality or using risky third-party libraries. Acceptable isolation techniques include sandboxing, encapsulation, containerization, and network-level isolation. These controls limit lateral movement and contain the blast radius if an attacker compromises one part of the application.
 
 Follow these guidelines:
 - Identify and document all application components that handle dangerous operations (e.g., file processing, deserialization, external API calls) or rely on known-risky third-party libraries.
 - Apply the strongest feasible isolation technique: sandboxed iframes for untrusted web content, separate processes or containers for high-risk server-side components, and network-level segmentation for microservices containing sensitive logic.
 - Enforce least-privilege access between isolated zones — each component should communicate only with the components it strictly requires.
 - Regularly review and update the list of risky components as new third-party vulnerabilities are disclosed.

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Applied
