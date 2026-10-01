---
name: t558-authenticate-all-other-components-before-any-network-commun
description: Authenticate the remote endpoint before exchanging data with it, and restrict which endpoints may be contacted.
---

# T558: Authenticate all other components before any network communication with them

**Category:** CODE_FIX
**SD Elements:** [T558](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T558/)
**Priority:** 9

**Finding:** The outbound HTTP call to an arbitrary image host presents no client credentials and performs no mutual authentication.

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
ALLOWED_IMAGE_HOSTS = {"cdn.restaurant.com"}


def _fetch_image(image_url: str) -> bytes:
    parsed = urlparse(image_url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_IMAGE_HOSTS:
        raise HTTPException(status_code=400, detail="Image host not allowed")

    response = requests.get(
        image_url,
        timeout=5,
        verify=certifi.where(),
        headers={"Authorization": f"Bearer {settings.CDN_TOKEN}"},
    )
    response.raise_for_status()
    return response.content
```

**Success Criteria:**
- Outbound calls go only to hosts on an allow-list over HTTPS.
- The remote server's certificate is validated against a pinned trust store.
- The service presents its own credential to the remote component.

**Status:** Applied
