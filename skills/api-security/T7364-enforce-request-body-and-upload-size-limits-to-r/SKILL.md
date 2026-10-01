---
name: t7364-enforce-request-body-and-upload-size-limits-to-resist-memo
description: Bound the size of any content the service downloads or accepts so a single request cannot exhaust process memory.
---

# T7364: Enforce request-body and upload size limits to resist memory-exhaustion DoS (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7364](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7364/)
**Priority:** 8

**Finding:** The remote image is downloaded and base64-encoded entirely in memory with no Content-Length check and no size cap.

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
MAX_IMAGE_BYTES = 2 * 1024 * 1024


def _image_url_to_base64(image_url: str) -> str:
    with requests.get(image_url, stream=True, timeout=5) as response:
        response.raise_for_status()
        declared = response.headers.get("Content-Length")
        if declared is not None and int(declared) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="Image too large")

        chunks, total = [], 0
        for chunk in response.iter_content(64 * 1024):
            total += len(chunk)
            if total > MAX_IMAGE_BYTES:
                raise HTTPException(status_code=413, detail="Image too large")
            chunks.append(chunk)

    return base64.b64encode(b"".join(chunks)).decode()
```

**Success Criteria:**
- The download is streamed and aborts once the byte ceiling is crossed.
- A declared Content-Length above the ceiling short-circuits before any body is read.
- A connect and read timeout is set on the outbound request.

**Status:** Applied
