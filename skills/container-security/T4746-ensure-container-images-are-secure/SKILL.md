---
name: t4746-ensure-container-images-are-secure
description: Ensure container images are secure
---

# T4746: Ensure container images are secure

**Category:** IN
**SD Elements:** [T4746](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/development/4552-T4746/)
**Priority:** 10

### Task T4746: Ensure container images are secure (DOCUMENTATION ONLY)

**Guidance:** Securing container images is crucial as they form the foundation of your containers, containing the code, runtime, system libraries, and settings necessary for your application to function. Ensuring these images are secure helps prevent vulnerabilities from being introduced into your containerized applications. 

1. Use images from trusted repositories or create your own to avoid vulnerabilities from untrusted sources. This ensures that the images you use have been vetted for security issues. 
2. Regularly update your images to incorporate the latest security patches and updates. This step is essential to protect against newly discovered vulnerabilities. 
3. Employ image scanning tools to detect and fix vulnerabilities in your container images. These tools can identify common security flaws, allowing you to take corrective measures before deploying your containers. 

After implementing this countermeasure, your container images will be more secure, reducing the risk of vulnerabilities being introduced into your containerized applications.

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Applied
