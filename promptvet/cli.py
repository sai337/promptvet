"""promptvet CLI.

  promptvet scan prompts.csv --out out/            # report.json, report.html, approved.csv, findings.sarif
  promptvet scan prompts.csv --skills 25           # also build a vetted SKILL.md pack
  promptvet scan skills/ --fail-on blocked         # CI gate: exit 1 if anything is blocked
  promptvet check "Ignore all previous instructions"   # one prompt
  promptvet serve --port 8080                      # HTTP API + UI
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from . import judge as judge_mod
from .core import PromptRecord, RuleSet, default_ruleset, scan, scan_one, summarize
from .io import load, write_approved_csv, write_json, write_sarif, write_skills
from .report import render_html


def _rules(path):
    return RuleSet.from_file(path) if path else default_ruleset()


def cmd_scan(a) -> int:
    recs = load(a.path)
    rs = _rules(a.rules)
    results = scan(recs, rs, dedupe=not a.no_dedupe, threshold=a.dup_threshold)
    if a.judge:
        if not judge_mod.configured():
            print("--judge needs PROMPTVET_JUDGE_BASE_URL and PROMPTVET_JUDGE_MODEL", file=sys.stderr)
            return 2
        text = {r.id: r for r in recs}
        for r in results:
            if r.tier == "review":
                r.judge = judge_mod.judge(r.title, text[r.id].text)
    summary = summarize(results)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    write_json(results, summary, str(out / "report.json"))
    (out / "report.html").write_text(render_html(results, summary, a.title,
                                                 f"Source: {a.source_name or a.path} · promptvet {__version__}"),
                                     encoding="utf-8")
    n_ok = write_approved_csv(recs, results, str(out / "approved.csv"))
    write_sarif(results, str(out / "findings.sarif"), a.path)
    made = write_skills(recs, results, str(out / "skills"), top=a.skills,
                        source_name=a.source_name or Path(a.path).name) if a.skills else []
    t = summary["tiers"]
    print(f"scanned {summary['total']}: approved {t['approved']} · review {t['review']} · blocked {t['blocked']}"
          f" · duplicates {summary['duplicates']} · avg trust {summary['avg_trust']}")
    print(f"wrote {out}/report.html, report.json, approved.csv ({n_ok}), findings.sarif"
          + (f", skills/ ({len(made)})" if made else ""))
    order = {"approved": 0, "review": 1, "blocked": 2}
    if a.fail_on and any(order[r.tier] >= order[a.fail_on] for r in results):
        return 1
    return 0


def cmd_check(a) -> int:
    text = a.text if a.text != "-" else sys.stdin.read()
    r = scan_one(PromptRecord("00000", a.title, text), _rules(a.rules))
    print(json.dumps(r.to_dict(), indent=1))
    return 1 if r.tier == "blocked" else 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="promptvet", description="Vet prompt and skill libraries.")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", help="scan a CSV/JSON file or a folder of prompts/skills")
    s.add_argument("path")
    s.add_argument("--out", default="promptvet-out")
    s.add_argument("--rules", help="YAML/JSON rules file (extend or disable defaults)")
    s.add_argument("--skills", type=int, default=0, help="build a SKILL.md pack from the top N approved prompts")
    s.add_argument("--fail-on", choices=["review", "blocked"])
    s.add_argument("--no-dedupe", action="store_true")
    s.add_argument("--dup-threshold", type=float, default=0.8)
    s.add_argument("--judge", action="store_true", help="LLM second opinion on review-tier prompts")
    s.add_argument("--title", default="Prompt library audit")
    s.add_argument("--source-name")
    s.set_defaults(fn=cmd_scan)
    c = sub.add_parser("check", help="check one prompt ('-' reads stdin)")
    c.add_argument("text")
    c.add_argument("--title", default="prompt")
    c.add_argument("--rules")
    c.set_defaults(fn=cmd_check)
    v = sub.add_parser("serve", help="HTTP API + UI")
    v.add_argument("--host", default="0.0.0.0")
    v.add_argument("--port", type=int, default=8080)
    v.set_defaults(fn=lambda a: __import__("promptvet.server", fromlist=["serve"]).serve(a.host, a.port) or 0)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
