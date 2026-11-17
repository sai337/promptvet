from promptvet.core import PromptRecord
from promptvet.dedupe import jaccard, near_duplicates, shingles


def test_shingles_and_jaccard():
    a, b = shingles("one two three four"), shingles("one two three five")
    assert 0 < jaccard(a, b) < 1 and jaccard(a, a) == 1.0


def test_near_duplicates_keeps_preferred():
    base = " ".join(f"word{i}" for i in range(60))
    recs = [PromptRecord("a", "a", base), PromptRecord("b", "b", base + " extra"), PromptRecord("c", "c", "totally different text here")]
    out = near_duplicates(recs, 0.8, prefer=lambda i: {"a": 1, "b": 5, "c": 0}[i])
    assert out == {"a": "b"}


def test_distinct_texts_not_duplicates():
    recs = [PromptRecord(str(i), "x", f"Act as role number {i}. " + " ".join(f"t{i}_{j}" for j in range(30))) for i in range(20)]
    assert near_duplicates(recs) == {}
