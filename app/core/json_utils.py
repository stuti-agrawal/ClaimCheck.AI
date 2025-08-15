# app/core/json_utils.py
from __future__ import annotations
import json, re

# Fast path: last {...} block
_LAST_JSON = re.compile(r"\{[\s\S]*\}\s*$")

def extract_json_obj(text: str) -> dict:
    s = text.strip()
    # 1) Try last-JSON regex (often enough)
    m = _LAST_JSON.search(s)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass

    # 2) Balanced-brace scan: find the largest valid JSON object
    best = None
    stack = 0
    start = None
    for i, ch in enumerate(s):
        if ch == '{':
            if stack == 0:
                start = i
            stack += 1
        elif ch == '}':
            if stack > 0:
                stack -= 1
                if stack == 0 and start is not None:
                    candidate = s[start:i+1]
                    try:
                        obj = json.loads(candidate)
                        best = obj  # keep last valid (usually the largest)
                    except Exception:
                        pass
    if best is not None:
        return best

    # 3) Try to strip common wrappers like code fences
    s2 = s.strip("` \n\t")
    try:
        return json.loads(s2)
    except Exception:
        pass

    # 4) Give up with a readable error
    raise ValueError("Could not extract JSON object from model text")
