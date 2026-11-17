"""Scanning, scoring and tiering. Standard library only, so it runs anywhere
(laptop, CI runner, serverless function, distroless container)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from typing import Iterable

from . import rules as default_rules

SEVERITY_PENALTY = {"high": 60, "medium": 25, "low": 5}
TIERS = ("approved", "review", "blocked")


@dataclass
class Finding:
    rule_id: str
    category: str
    severity: str
    message: str
    excerpt: str


@dataclass
class PromptRecord:
    id: str
    title: str
    text: str
    source: str = ""
    contributor: str = ""
    kind: str = "TEXT"
    for_devs: bool = False


@dataclass
class Result:
    id: str
    title: str
    tier: str
    trust: int
    safety: int
    quality: int
    category: str
    findings: list[Finding] = field(default_factory=list)
    quality_signals: list[str] = field(default_factory=list)
    duplicate_of: str | None = None
    chars: int = 0
    variables: list[str] = field(default_factory=list)
    judge: dict | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


class RuleSet:
    """Compiled rules. Load custom rules with RuleSet.from_file(path)."""

    def __init__(self, risk_rules=None, quality_signals=None, categories=None):
        self.risk_rules = []
        for r in risk_rules or default_rules.RISK_RULES:
            self.risk_rules.append({
                **r,
                "_re": re.compile(r["pattern"], re.I),
                "_unless": re.compile(r["unless"], re.I) if r.get("unless") else None,
            })
        self.quality = [(i, w, re.compile(p, re.I), label)
                        for i, w, p, label in (quality_signals or default_rules.QUALITY_SIGNALS)]
        self.categories = {k: re.compile(v, re.I) for k, v in (categories or default_rules.CATEGORIES).items()}
        self.defensive = re.compile(default_rules.DEFENSIVE_CONTEXT, re.I)
        self.negation = re.compile(default_rules.NEGATION_NEAR, re.I)
        self.placeholder = re.compile(default_rules.SECRET_PLACEHOLDER, re.I)
        self.genre = re.compile(default_rules.DEFENSIVE_GENRE, re.I)
        self.visual = re.compile(default_rules.VISUAL_DETECT, re.I)
        self.visual_quality = [(i, w, re.compile(p, re.I), label) for i, w, p, label in default_rules.VISUAL_SIGNALS]

    @classmethod
    def from_file(cls, path: str) -> "RuleSet":
        with open(path, encoding="utf-8") as f:
            if path.endswith((".yaml", ".yml")):
                import yaml  # optional dependency
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        extra = data.get("risk_rules", [])
        disabled = set(data.get("disable", []))
        base = [r for r in default_rules.RISK_RULES if r["id"] not in disabled]
        if data.get("replace_defaults"):
            base = []
        return cls(risk_rules=base + extra)


_DEFAULT: RuleSet | None = None


def default_ruleset() -> RuleSet:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = RuleSet()
    return _DEFAULT


VAR_RE = re.compile(r"\$\{([^}:]{1,40})(?::[^}]*)?\}|\{\{([^}]{1,40})\}\}")


def find_variables(text: str) -> list[str]:
    seen = []
    for m in VAR_RE.finditer(text):
        v = (m.group(1) or m.group(2)).strip()
        if v and v not in seen:
            seen.append(v)
    return seen[:20]


_DOWN = {"high": "medium", "medium": "low", "low": "low"}
_QUOTE = re.compile(r"[\"'`\u201c\u2018]\s*$")


def _defensive(text: str, start: int, rs: RuleSet) -> bool:
    """True when a match is quoted, negated or described as something to detect."""
    line = text[text.rfind("\n", 0, start) + 1:start].lower()
    return bool(_QUOTE.search(text[max(0, start - 3):start])
                or "negative" in line
                or rs.negation.search(text[max(0, start - 50):start])
                or rs.defensive.search(text[max(0, start - 160):start]))


def risk_findings(text: str, rs: RuleSet) -> list[Finding]:
    out = []
    defensive_genre = bool(rs.genre.search(text[:500]))
    for r in rs.risk_rules:
        m = None
        for cand in r["_re"].finditer(text):
            if r["category"] == "secret" and rs.placeholder.search(cand.group(0)):
                continue
            m = cand
            break
        if not m:
            continue
        if r["_unless"] is not None and r["_unless"].search(text):
            continue
        severity, message = r["severity"], r["message"]
        if r.get("context_downgrade"):
            # use the most dangerous occurrence: any non-defensive hit keeps full severity
            hits = [c for c in r["_re"].finditer(text)]
            if hits and (defensive_genre or all(_defensive(text, c.start(), rs) for c in hits)):
                severity = _DOWN[severity]
                message += " (only in a quoted, negated or defensive context)"
        s, e = max(0, m.start() - 40), min(len(text), m.end() + 40)
        excerpt = re.sub(r"\s+", " ", text[s:e]).strip()
        # never echo a secret back in a report
        if r["category"] == "secret":
            excerpt = "[redacted]"
        out.append(Finding(r["id"], r["category"], severity, message, excerpt[:160]))
    return out


def is_visual(text: str, rs: RuleSet) -> bool:
    return len(set(m.group(0).lower() for m in rs.visual.finditer(text[:4000]))) >= 3


def quality_score(text: str, rs: RuleSet) -> tuple[int, list[str]]:
    score, hits = 0, []
    signals = rs.visual_quality if is_visual(text, rs) else rs.quality
    if signals is rs.visual_quality:
        hits.append("Visual rubric")
    for _id, weight, rx, label in signals:
        if rx.search(text):
            score += weight
            hits.append(label)
    n = len(text.strip())
    if 150 <= n <= 6000:
        score += 20
        hits.append("Good length")
    elif 80 <= n < 150 or 6000 < n <= 15000:
        score += 10
    letters = [c for c in text if c.isalpha()]
    if letters and sum(c.isupper() for c in letters) / len(letters) > 0.5:
        score -= 15  # shouting
    return max(0, min(100, score)), hits


def classify(title: str, text: str, rs: RuleSet) -> str:
    blob = f"{title} {title} {text[:1500]}"
    best, best_n = "general", 0
    for name, rx in rs.categories.items():
        n = len(rx.findall(blob))
        if n > best_n:
            best, best_n = name, n
    return best


def scan_one(rec: PromptRecord, rs: RuleSet | None = None) -> Result:
    rs = rs or default_ruleset()
    text = f"{rec.title}\n{rec.text}"
    findings = risk_findings(text, rs)
    q, signals = quality_score(rec.text, rs)
    penalty = sum(SEVERITY_PENALTY[f.severity] for f in findings)
    safety = max(0, 100 - penalty)
    trust = round(0.6 * safety + 0.4 * q)
    sev = {f.severity for f in findings}
    if "high" in sev:
        tier = "blocked"
    elif "medium" in sev or q < 40:
        tier = "review"
    else:
        tier = "approved"
    return Result(rec.id, rec.title, tier, trust, safety, q, classify(rec.title, rec.text, rs),
                  findings, signals, None, len(rec.text), find_variables(rec.text))


def scan(records: Iterable[PromptRecord], rs: RuleSet | None = None, dedupe: bool = True,
         threshold: float = 0.8) -> list[Result]:
    from .dedupe import near_duplicates
    rs = rs or default_ruleset()
    recs = list(records)
    results = [scan_one(r, rs) for r in recs]
    if dedupe:
        by_id = {r.id: r for r in results}
        for dup_id, keep_id in near_duplicates(recs, threshold, prefer=lambda i: by_id[i].trust).items():
            res = by_id[dup_id]
            res.duplicate_of = keep_id
            if res.tier == "approved":
                res.tier = "review"
    return results


def summarize(results: list[Result]) -> dict:
    from collections import Counter
    tiers = Counter(r.tier for r in results)
    cats = Counter(f.category for r in results for f in r.findings)
    rules_hit = Counter(f.rule_id for r in results for f in r.findings)
    by_cat = Counter(r.category for r in results)
    approved_by_cat = Counter(r.category for r in results if r.tier == "approved")
    n = len(results) or 1
    return {
        "total": len(results),
        "tiers": {t: tiers.get(t, 0) for t in TIERS},
        "tier_pct": {t: round(100 * tiers.get(t, 0) / n, 1) for t in TIERS},
        "risk_categories": dict(cats.most_common()),
        "top_rules": dict(rules_hit.most_common(10)),
        "duplicates": sum(1 for r in results if r.duplicate_of),
        "avg_trust": round(sum(r.trust for r in results) / n, 1),
        "avg_quality": round(sum(r.quality for r in results) / n, 1),
        "categories": dict(by_cat.most_common()),
        "approved_by_category": dict(approved_by_cat.most_common()),
    }
