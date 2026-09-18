---
name: t2615-limit-network-access-by-blocking-connect
description: Limit network access by blocking connections from unknown IP addresses (PostgreSQL)
---

# T2615: Limit network access by blocking connections from unknown IP addresses (PostgreSQL)

**Category:** IN
**SD Elements:** [T2615](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T2615/)
**Priority:** 8

### Task T2615: Limit network access by blocking connections from unknown IP addresses (PostgreSQL) (DOCUMENTATION ONLY)

**Guidance:** Verify that the __pg_hba.conf__ configuration file uses rules to restrict access based on username, database, and source IP. 

A simple policy might:
- Permit a local user to have wide-ranging access
- Require a secure authentication method
- Allow a specific range of IP addresses to connect remotely to a specific database
 
Here's an example:

	# TYPE    DATABASE   USER            ADDRESS          METHOD
	host      all        postgres-admin  127.001/32     scram-sha-256
	hostssl   store-db   store-app       192.168.12.0/24  scram-sha-256
	host      all        all             all              reject

PostgreSQL uses the first matching rule. Here, the `postgres-admin` user can only log in from the local host (`127.001`), while the `store-app` user can log in from any IP beginning with `192.168.12` when accessing the `store-db` database.

Use a database value of `samerole` to allow users to access just the database that has the same name as the user account:

	hostssl   samerole    all            192.168.12.0/24  scram-sha-256

## Note
Network restrictions with the __pg.hba.conf__ file should be set in __addition__ to the usual network protection measures, such as subnetting and firewalls. For example, a good firewall rule would reject TCP traffic going to the database server on port 5432 unless it originates from the application server's IP.

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Applied
