"""Build-time audit: fetch a pinned prompts.chat snapshot and render the public report.

Used by the Vercel build (vercel.json buildCommand) and by `make audit`.
Pinned commit = reproducible numbers. Bump PROMPTS_CHAT_SHA to refresh.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from promptvet import __version__  # noqa: E402
from promptvet.core import scan, summarize  # noqa: E402
from promptvet.io import load  # noqa: E402
from promptvet.report import render_html  # noqa: E402

SHA = os.getenv("PROMPTS_CHAT_SHA", "36c1131e85e4ff08ce4d908f0e907e3dbdd019a5")
URL = f"https://raw.githubusercontent.com/f/prompts.chat/{SHA}/prompts.csv"


def main() -> int:
    out = Path(os.getenv("OUT_DIR", ROOT / "public"))
    out.mkdir(parents=True, exist_ok=True)
    src = Path(os.getenv("PROMPTS_CSV", "/tmp/prompts.csv"))
    if not src.exists():
        urllib.request.urlretrieve(URL, src)
    recs = load(str(src))
    res = scan(recs)
    s = summarize(res)
    s["source"] = {"repo": "f/prompts.chat", "commit": SHA, "license": "CC0-1.0"}
    s["promptvet_version"] = __version__
    (out / "summary.json").write_text(json.dumps(s, indent=1))
    (out / "report.html").write_text(render_html(
        res, s, "Auditing the world's largest open prompt library",
        f"prompts.chat @ {SHA[:7]} (CC0) · {s['total']} prompts · promptvet {__version__}"), encoding="utf-8")
    print(json.dumps({k: s[k] for k in ("total", "tiers", "duplicates", "avg_trust")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
