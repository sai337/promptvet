"""Near-duplicate detection with MinHash + LSH banding (stdlib only)."""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict

NUM_PERM = 64
BANDS = 16  # 16 bands x 4 rows -> ~0.5 candidate threshold, verified with exact Jaccard
_MASK = (1 << 64) - 1
_SEEDS = [int.from_bytes(hashlib.blake2b(str(i).encode(), digest_size=8).digest(), "big") | 1
          for i in range(NUM_PERM)]


def _norm(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def shingles(text: str, k: int = 3) -> set[str]:
    w = _norm(text)
    if len(w) < k:
        return {" ".join(w)} if w else set()
    return {" ".join(w[i:i + k]) for i in range(len(w) - k + 1)}


def _h(s: str) -> int:
    return int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), "big")


def minhash(sh: set[str]) -> tuple[int, ...]:
    base = [_h(s) for s in sh] or [0]
    return tuple(min(((b ^ seed) * 0x9E3779B97F4A7C15) & _MASK for b in base) for seed in _SEEDS)


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def near_duplicates(records, threshold: float = 0.8, prefer=None) -> dict[str, str]:
    """Return {duplicate_id: kept_id}. `prefer(id)` picks which copy to keep (higher wins)."""
    sh = {r.id: shingles(r.text) for r in records}
    rows = NUM_PERM // BANDS
    buckets: dict[tuple, list[str]] = defaultdict(list)
    for rid, s in sh.items():
        if not s:
            continue
        sig = minhash(s)
        for b in range(BANDS):
            buckets[(b, sig[b * rows:(b + 1) * rows])].append(rid)

    parent: dict[str, str] = {}

    def find(x):
        while parent.get(x, x) != x:
            x = parent[x]
        return x

    checked = set()
    for ids in buckets.values():
        if len(ids) < 2 or len(ids) > 200:
            continue
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                pair = (ids[i], ids[j])
                if pair in checked:
                    continue
                checked.add(pair)
                if jaccard(sh[ids[i]], sh[ids[j]]) >= threshold:
                    ra, rb = find(ids[i]), find(ids[j])
                    if ra != rb:
                        parent[rb] = ra

    groups: dict[str, list[str]] = defaultdict(list)
    for rid in sh:
        groups[find(rid)].append(rid)
    out = {}
    order = {r.id: n for n, r in enumerate(records)}
    for members in groups.values():
        if len(members) < 2:
            continue
        keep = max(members, key=lambda m: ((prefer(m) if prefer else 0), -order[m]))
        for m in members:
            if m != keep:
                out[m] = keep
    return out
