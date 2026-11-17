"""Transport-free API logic shared by the Vercel function and the container server."""
from __future__ import annotations

from . import __version__
from .core import PromptRecord, scan, scan_one, summarize

MAX_CHARS = 50_000
MAX_ITEMS = 500


def handle(payload: dict) -> tuple[int, dict]:
    if not isinstance(payload, dict):
        return 400, {"error": "Body must be a JSON object."}
    if "prompts" in payload:
        items = payload["prompts"]
        if not isinstance(items, list) or not items:
            return 400, {"error": "'prompts' must be a non-empty list."}
        if len(items) > MAX_ITEMS:
            return 413, {"error": f"At most {MAX_ITEMS} prompts per call."}
        recs = []
        for i, it in enumerate(items):
            if not isinstance(it, dict) or not isinstance(it.get("prompt", ""), str):
                return 400, {"error": f"Item {i} needs a string 'prompt'."}
            if len(it.get("prompt", "")) > MAX_CHARS:
                return 413, {"error": f"Item {i} is longer than {MAX_CHARS} characters."}
            recs.append(PromptRecord(f"{i:05d}", str(it.get("title", f"prompt {i}"))[:200], it.get("prompt", "")))
        res = scan(recs)
        return 200, {"version": __version__, "summary": summarize(res), "results": [r.to_dict() for r in res]}
    text = payload.get("prompt")
    if not isinstance(text, str) or not text.strip():
        return 400, {"error": "Send {\"prompt\": \"...\"} or {\"prompts\": [...]}."}
    if len(text) > MAX_CHARS:
        return 413, {"error": f"Prompt is longer than {MAX_CHARS} characters."}
    r = scan_one(PromptRecord("00000", str(payload.get("title", "pasted prompt"))[:200], text))
    return 200, {"version": __version__, "result": r.to_dict()}
