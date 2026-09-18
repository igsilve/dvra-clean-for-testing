---
name: t2601-use-transparent-data-encryption-with-ent
description: Use Transparent Data Encryption with Enterprise Databases
---

# T2601: Use Transparent Data Encryption with Enterprise Databases

**Category:** IN
**SD Elements:** [T2601](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T2601/)
**Priority:** 8

### Task T2601: Use Transparent Data Encryption with Enterprise Databases (DOCUMENTATION ONLY)

**Guidance:** Enterprise databases like Oracle, Microsoft SQL Server, and IBM employ Transparent Data Encryption (TDE) to safeguard sensitive data. TDE allows for seamless decryption during access, managed through the database's administrative interface. It protects against network attacks and theft of storage media by ensuring data remains encrypted until accessed by authorized users, enhancing overall security.

- Enable TDE for entire tables, columns within a table, and or individual cells within a table when appropriate. 

Note: TDE is implemented differently in each enterprise database product. Check the documentation to find out how to implement it in your environment.

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Documented
