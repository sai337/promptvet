import io
import json

from promptvet import judge


class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def fake(content):
    def opener(req, timeout=0):
        body = json.loads(req.data)
        assert body["temperature"] == 0 and "<prompt" in body["messages"][1]["content"]
        return Resp(json.dumps({"choices": [{"message": {"content": content}}]}).encode())
    return opener


def test_judge_parses_and_sanitizes(monkeypatch):
    monkeypatch.setenv("PROMPTVET_JUDGE_BASE_URL", "http://gw.local/v1")
    monkeypatch.setenv("PROMPTVET_JUDGE_MODEL", "small")
    assert judge.configured()
    assert judge.judge("t", "x", opener=fake('ok {"verdict": "reject", "reason": "jailbreak"}'))["verdict"] == "reject"
    assert judge.judge("t", "x", opener=fake('{"verdict": "yolo"}'))["verdict"] == "review"
    assert judge.judge("t", "x", opener=fake("not json"))["verdict"] == "review"
