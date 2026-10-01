---
name: t3915-enforce-separation-of-deployment-configuration-files-githu
description: Move deployment values out of the committed compose file into per-environment configuration supplied at deploy time.
---

# T3915: Enforce separation of deployment configuration files (GitHub)

**Category:** CODE_FIX
**SD Elements:** [T3915](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T3915/)
**Priority:** 8

**Finding:** Deployment configuration and credentials are inlined in the committed compose file rather than separated per environment.

**Code to Fix:**
```yaml
# docker-compose.yml lines 15-20
    environment:
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=password
      - POSTGRES_SERVER=db
      - POSTGRES_PORT=5432
      - POSTGRES_DB=restaurant
```

**Required Fix:**
```yaml
# docker-compose.yml
  web:
    env_file:
      - ./deploy/${DEPLOY_ENV}.env      # not committed; provided by the deploy pipeline
  db:
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
    secrets:
      - postgres_password

secrets:
  postgres_password:
    external: true
```

**Success Criteria:**
- No environment-specific value or credential is committed to the repository.
- Each environment has its own configuration source resolved at deploy time.
- `.env` files are listed in .gitignore.

**Status:** Applied
