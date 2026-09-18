---
name: t2621-use-file-volume-encryption-and-consider
description: Use file volume encryption and consider in-database encryption with pgcrypto (PostgreSQL)
---

# T2621: Use file volume encryption and consider in-database encryption with pgcrypto (PostgreSQL)

**Category:** IN
**SD Elements:** [T2621](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T2621/)
**Priority:** 8

### Task T2621: Use file volume encryption and consider in-database encryption with pgcrypto (PostgreSQL) (DOCUMENTATION ONLY)

**Guidance:** PostgreSQL does not have built-in encryption. Regulations or business considerations may require at-rest encryption for your data. To satisfy this requirement, you may use these options:

- Use Transparent Data Encryption (TDE). This feature is only available in EnterpriseDB's hosted version of PostgreSQL.
- Encrypt the data volume using operating system features, such as FDE (Full Disk Encryption) in Linux or BitLocker in Windows. This is recommended, but it may not be sufficient to meet security requirements, as users with OS access can bypass OS-level encryption.
- Encrypt data manually using the __pgcrypto__ extension. This adds complexity and requires you to safely store the encryption keys you use.

## Note
To check if `pgcrypto` is installed, use this command:

	SELECT * FROM pg_available_extensions WHERE name='pgcrypto'; 

To enable `pgcrypto`, use this command:

	CREATE EXTENSION pgcrypto;

Once __pgcrypto__ is enabled, you can use the `crypt` and decrypt` functions in your SQL statements. However, __pgcrypto__ is only a viable approach if you securely store and manage the keys that it uses.

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Documented
