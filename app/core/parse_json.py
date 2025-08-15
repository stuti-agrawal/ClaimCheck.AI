import json
import re
from typing import Any, Optional, Union


def _strip_trailing_commas(s: str) -> str:
    """Remove trailing commas before ] or }"""
    return re.sub(r',\s*(\]|\})', r'\1', s)


def _balance_brackets(s: str) -> str:
    """Balance unclosed braces/brackets for incomplete JSON."""
    opens = {"{": "}", "[": "]"}
    stack = []
    for ch in s:
        if ch in opens:
            stack.append(opens[ch])
        elif ch in opens.values() and stack and ch == stack[-1]:
            stack.pop()
    return s + "".join(reversed(stack))


def _find_json_like(text: str) -> Optional[str]:
    """
    Finds the first plausible JSON substring in the text.
    Can match dict `{...}` or list `[...]`.
    """
    m = re.search(r'(\{|\[)', text)
    if not m:
        return None
    start = m.start()

    # Try to find last closing bracket
    last_brace = max(text.rfind("}"), text.rfind("]"))
    if last_brace == -1:
        last_brace = len(text)

    candidate = text[start:last_brace + 1]
    return candidate.strip()


def parse_json_anywhere(
    text: str,
    root_key: Optional[str] = None
) -> Union[dict, list, None]:
    """
    Universal JSON parser for LLM output.
    - Accepts JSON object or array
    - Repairs common LLM formatting issues
    - Optionally extracts by `root_key`
    - Handles incomplete JSON (unbalanced braces/brackets)

    Args:
        text: raw LLM output
        root_key: if provided, returns only the value at that key
                  (works even if wrapped in an array)

    Returns:
        Parsed JSON object, list, or None if all parsing fails
    """
    if not text:
        return None

    # 1) Direct parse attempt
    try:
        data = json.loads(text)
        return _extract_root(data, root_key)
    except Exception:
        pass

    # 2) Extract JSON-ish substring from text
    candidate = _find_json_like(text)
    if candidate:
        # repair commas & bracket balance
        repaired = _balance_brackets(_strip_trailing_commas(candidate))

        for blob in (candidate, repaired):
            try:
                data = json.loads(blob)
                return _extract_root(data, root_key)
            except Exception:
                continue

    return None


def _extract_root(data: Any, root_key: Optional[str]) -> Any:
    """Get data by root key if needed; handle array-wrapped objects."""
    if not root_key:
        return data

    if isinstance(data, dict) and root_key in data:
        return data
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and root_key in item:
                return item
    return {root_key: []}


import re, json
from json import JSONDecoder
from typing import Any, Optional

_JSON_OBJ = re.compile(r'\{')

def iter_json_objects(s: str):
    """Yield every JSON object found in a string."""
    dec = JSONDecoder()
    for m in _JSON_OBJ.finditer(s or ""):
        try:
            obj, _ = dec.raw_decode(s, m.start())
            yield obj
        except Exception:
            continue

def strip_footers(text: str) -> str:
    """Remove common model footnotes like '*Note:' or 'Note:'."""
    lines = (text or "").splitlines()
    clean = []
    for ln in lines:
        if ln.lstrip().lower().startswith(("*note", "note:")):
            break
        clean.append(ln)
    return "\n".join(clean)

def merge_json_blocks(blocks: list[dict], root_key: str) -> dict:
    """
    Merge multiple dicts with the same list-valued root_key, 
    de-dupe by object identity (stringified) for now.
    """
    merged = []
    seen = set()
    for b in blocks:
        vals = b.get(root_key) or []
        if not isinstance(vals, list):
            continue
        for v in vals:
            key = json.dumps(v, sort_keys=True)
            if key not in seen:
                merged.append(v)
                seen.add(key)
    return {root_key: merged}

def parse_json_anywhere(text: str, root_key: Optional[str] = None) -> dict[str, Any]:
    """
    Parse potentially messy LLM output into JSON. If root_key is given, 
    only keep JSON objects that have that key (list-valued).
    """
    if not text:
        return {root_key or "": []}
    text = strip_footers(text.strip())

    # try naive load first
    try:
        obj = json.loads(text)
        if not root_key or root_key in obj:
            return obj
    except Exception:
        pass

    blocks = []
    for obj in iter_json_objects(text):
        if not isinstance(obj, dict):
            continue
        if root_key and root_key not in obj:
            continue
        blocks.append(obj)

    if not blocks:
        return {root_key or "": []}
    return merge_json_blocks(blocks, root_key) if root_key else blocks[0]
