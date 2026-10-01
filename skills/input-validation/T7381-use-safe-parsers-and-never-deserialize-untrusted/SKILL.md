---
name: t7381-use-safe-parsers-and-never-deserialize-untrusted-binary-da
description: Parse remote content with a strict, format-aware parser and never deserialize untrusted binary formats.
---

# T7381: Use safe parsers and never deserialize untrusted binary data (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7381](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7381/)
**Priority:** 10

**Finding:** Untrusted remote binary content is ingested and re-encoded with no parser restrictions.

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
with Image.open(io.BytesIO(content)) as image:
    if image.format not in ALLOWED_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported image format")
    image.verify()

# Nothing in the request path calls pickle.loads, yaml.load or marshal.loads.
```

**Success Criteria:**
- No untrusted bytes reach pickle, marshal or an unsafe YAML loader.
- Binary content is validated by a parser that fails closed on malformed input.
- Parsers are configured with size and recursion limits.

**Status:** Applied
