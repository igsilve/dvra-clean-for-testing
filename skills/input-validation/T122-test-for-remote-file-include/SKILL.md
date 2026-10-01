---
name: t122-test-for-remote-file-include
description: Restrict which remote locations the service may load content from.
---

# T122: Test for remote file include

**Category:** CODE_FIX
**SD Elements:** [T122](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T122/)
**Priority:** 10

**Finding:** A caller-supplied URL is fetched and its bytes are embedded in the application's own responses.

**Code to Fix:**
```python
# app/apis/menu/utils.py lines 9-13
def _image_url_to_base64(image_url: str):
    response = requests.get(image_url, stream=True)
    encoded_image = base64.b64encode(response.content).decode()

    return encoded_image
```

**Required Fix:**
```python
# app/apis/menu/utils.py
ALLOWED_IMAGE_HOSTS = {"cdn.restaurant.com"}


def _validate_image_url(image_url: str) -> str:
    parsed = urlparse(image_url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_IMAGE_HOSTS:
        raise HTTPException(status_code=400, detail="Image host not allowed")
    return image_url
```

**Success Criteria:**
- Remote content is loaded only from hosts on an allow-list.
- Non-HTTPS schemes such as file:, gopher: and ftp: are rejected.
- A URL pointing at an internal address is rejected.

**Status:** Applied
