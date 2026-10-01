---
name: t4749-monitor-containers-in-real-time
description: Monitor running containers for anomalous behaviour in real time.
---

### Task T4749: Monitor containers in real-time (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T4749](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4749/)
**Priority:** 10

**Guidance:** Runtime monitoring should observe process execution, network connections and file writes inside containers, alerting on behaviour that departs from the expected profile such as a shell spawning inside an application container.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, app/init_app.py, Dockerfile
- Found: No runtime security agent, log shipping or alerting is configured for the containers.
- Missing: A runtime monitoring agent, its deployment and an alert destination.
- Conclusion: Runtime container monitoring is a security platform capability deployed alongside the workload, not code in this repository.

**Recommended Action:** The security operations team should deploy runtime monitoring to the container hosts.

**Status:** Documented
