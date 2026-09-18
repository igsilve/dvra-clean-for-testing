---
name: t4600-establish-out-of-band-communications-cha
description: Establish Out-of-Band Communications Channel
---

# T4600: Establish Out-of-Band Communications Channel

**Category:** IN
**SD Elements:** [T4600](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/architecture-design/4552-T4600/)
**Priority:** 10

### Task T4600: Establish Out-of-Band Communications Channel (DOCUMENTATION ONLY)

**Guidance:** Have alternative methods to support communication requirements during communication failures and data integrity attacks. 

1. Identify critical communication channels and data flows essential for operations.
2. Determine acceptable downtime and data integrity thresholds for different systems.
3. Design redundant communication channels: 

    - Physical redundancy: Deploy backup communication infrastructure, such as secondary networks (e.g., satellite links, cellular data, or alternative wired connections).
    - Protocol redundancy: Use alternative communication protocols (e.g., MQTT, Zigbee, LoRaWAN) in case primary ones are compromised.

4. Implement fallback mechanisms, such as offline data storage or batch processing.

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Documented
