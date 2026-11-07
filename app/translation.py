"""Translate display-only LLM text without changing the audited English record."""
import json
import re

from . import llm

_CACHE = {}
_PROTECTED = re.compile(
    r"\[[A-Za-z0-9:.,\- ]+\]|"
    r"\b\d{1,2}(?:-\d{1,2})?\s+"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
    r"(?:\s+\d{4})?\b|"
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b|"
    r"\bQ[1-4]\s+\d{4}\b|"
    r"S\$\d[\d,]*(?:\.\d+)?(?:-\d+(?:\.\d+)?)?M?|"
    r"\d[\d,]*(?:\.\d+)?(?:-\d+(?:\.\d+)?)*%?",
    re.IGNORECASE,
)


def _mask(text):
    protected = []

    def mask(match):
        protected.append(match.group())
        return "{{T" + str(len(protected) - 1) + "}}"

    return _PROTECTED.sub(mask, text), protected


def _restore(result, protected):
    if not isinstance(result, str):
        return None
    expected = ["{{T" + str(i) + "}}" for i in range(len(protected))]
    if sorted(re.findall(r"\{\{T\d+\}\}", result)) != sorted(expected):
        return None
    for i, token in enumerate(protected):
        result = result.replace("{{T" + str(i) + "}}", token)
    return result.strip()


def to_chinese(text):
    if not isinstance(text, str) or not text.strip() or len(text) > 10000 or not llm.available():
        return {"text": text, "translated": False}
    if text in _CACHE:
        return {"text": _CACHE[text], "translated": True}

    masked, protected = _mask(text)
    system = ("Translate the supplied project-management text into natural Simplified Chinese. "
              "Preserve every {{Tn}} placeholder exactly once, in the right context. "
              "Preserve names, acronyms, risk IDs and meaning. Do not add facts. "
              "Return only the translation, with no preface or Markdown fence.")
    result, _ = llm.chat("translation", system, masked, max_tokens=1800)
    result = _restore(result, protected)
    if not result:
        return {"text": text, "translated": False}
    _CACHE[text] = result
    return {"text": _CACHE[text], "translated": True}


def many_to_chinese(texts):
    """Translate a bounded batch for one UI view; preserve IDs and figures exactly."""
    output = list(texts)
    if not llm.available():
        return output
    pending = [(i, value) for i, value in enumerate(texts)
               if isinstance(value, str) and value.strip() and value not in _CACHE]
    for i, value in enumerate(texts):
        if value in _CACHE:
            output[i] = _CACHE[value]
    while pending:
        batch, size = [], 0
        while pending and len(batch) < 20 and size + len(pending[0][1]) < 4500:
            index, value = pending.pop(0)
            masked, protected = _mask(value)
            batch.append((index, value, protected, masked))
            size += len(value)
        if not batch:  # one unusually long text; use the single-text path
            index, value = pending.pop(0)
            output[index] = to_chinese(value)["text"]
            continue
        request = {"items": [{"id": index, "text": masked} for index, _, _, masked in batch]}
        system = ("Translate every item into natural Simplified Chinese. Return JSON with a "
                  "translations array of objects {id, text}. Keep each id unchanged. "
                  "Preserve each {{Tn}} placeholder exactly once within its own item. "
                  "Do not add facts, omit items, or translate names and acronyms.")
        data, _ = llm.chat_json("translation", system, json.dumps(request, ensure_ascii=False), max_tokens=4000)
        found = {str(item.get("id")): item.get("text") for item in data.get("translations", [])
                 if isinstance(item, dict)} if isinstance(data, dict) else {}
        for index, value, protected, _ in batch:
            result = _restore(found.get(str(index)), protected)
            if result:
                output[index] = result
                _CACHE[value] = result
    return output
