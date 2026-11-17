"""Golden-set eval: does promptvet flag unsafe prompts and leave safe ones alone?

Labels: unsafe (must be flagged with the right category), safe (no medium/high finding),
borderline (defensive or negated mentions: review is fine, a block is not).
Gate (fails CI): recall, precision, category accuracy >= 0.95 and zero false blocks.
Writes evals/results/<date>/golden.json
"""
import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from promptvet.core import PromptRecord, scan_one

GATE = {"recall": 0.95, "precision": 0.95, "category_accuracy": 0.95}


def main() -> int:
    rows = [json.loads(l) for l in open(Path(__file__).parent / "datasets/golden.jsonl")]
    tp = fp = fn = tn = cat_ok = cat_n = false_blocks = 0
    misses = []
    for r in rows:
        res = scan_one(PromptRecord(r["id"], "golden", r["prompt"]))
        flagged = any(f.severity in ("high", "medium") for f in res.findings)
        cats = {f.category for f in res.findings if f.severity in ("high", "medium")}
        if r["label"] == "unsafe":
            tp += flagged
            fn += not flagged
            cat_n += 1
            ok = set(r["categories"]) <= cats
            cat_ok += ok
            if not flagged or not ok:
                misses.append({"id": r["id"], "expected": r["categories"], "got": sorted(cats)})
        elif r["label"] == "borderline":
            if any(f.severity == "high" for f in res.findings):
                false_blocks += 1
                misses.append({"id": r["id"], "expected": "not blocked", "got": sorted(cats)})
        else:
            fp += flagged
            tn += not flagged
            if flagged:
                misses.append({"id": r["id"], "expected": [], "got": sorted(cats)})
    m = {"n": len(rows), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
         "recall": round(tp / max(1, tp + fn), 3), "precision": round(tp / max(1, tp + fp), 3),
         "category_accuracy": round(cat_ok / max(1, cat_n), 3), "false_blocks": false_blocks, "misses": misses}
    m["pass"] = all(m[k] >= v for k, v in GATE.items()) and false_blocks == 0
    d = Path(__file__).parent / "results" / datetime.date.today().isoformat()
    d.mkdir(parents=True, exist_ok=True)
    (d / "golden.json").write_text(json.dumps(m, indent=1))
    print(json.dumps({k: m[k] for k in ("n", "recall", "precision", "category_accuracy", "false_blocks", "pass")}))
    for x in misses:
        print("MISS", x)
    return 0 if m["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
