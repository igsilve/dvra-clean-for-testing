---
name: t156-validate-certificate-and-its-chain-of-trust-properly
description: Validate the server certificate and its chain explicitly on every outbound TLS call.
---

# T156: Validate certificate and its chain of trust properly

**Category:** CODE_FIX
**SD Elements:** [T156](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T156/)
**Priority:** 7

**Finding:** requests.get is called on a caller-supplied URL with no explicit certificate verification or CA bundle configuration.

**Code to Fix:**
```python
# app/apis/menu/utils.py lines 9-11
def _image_url_to_base64(image_url: str):
    response = requests.get(image_url, stream=True)
    encoded_image = base64.b64encode(response.content).decode()
```

**Required Fix:**
```python
# app/apis/menu/utils.py
import certifi

session = requests.Session()
session.verify = certifi.where()      # explicit CA bundle, never False


def _fetch_image(image_url: str) -> bytes:
    response = session.get(image_url, timeout=5, allow_redirects=False)
    response.raise_for_status()
    return response.content
```

**Success Criteria:**
- `verify=False` appears nowhere in the codebase.
- The CA bundle is pinned explicitly rather than inherited from the environment.
- A connection to a host with an untrusted certificate fails.

**Status:** Applied
