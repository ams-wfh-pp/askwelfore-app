import pytest
import evaluate_coach as evaluation
from kitchen_coach import KitchenCoach


def test_dry_run_never_calls_provider(monkeypatch, capsys):
    monkeypatch.setattr(evaluation, "run", lambda *a: pytest.fail("Paid run attempted"))
    assert evaluation.main(["--suite", "pilot"]) == 0
    assert "6 API calls" in capsys.readouterr().out
    assert evaluation.main(["--suite", "full"]) == 0
    assert "20 API calls" in capsys.readouterr().out


def test_live_requires_approval_and_key(monkeypatch):
    monkeypatch.delenv("COACH_EVAL_APPROVED", raising=False)
    with pytest.raises(SystemExit):
        evaluation.main(["--live"])
    monkeypatch.setenv("COACH_EVAL_APPROVED", "YES")
    monkeypatch.delenv("COACH_EVAL_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        evaluation.main(["--live"])


@pytest.mark.parametrize("suite,count", [("pilot", 6), ("full", 20)])
def test_evaluation_evidence_and_counts(tmp_path, suite, count):
    calls = []
    def factory(key, model, reasoning, observe):
        def generate(instructions, messages, max_output_tokens):
            calls.append((model, reasoning, dict(instructions=instructions, messages=messages, max_output_tokens=max_output_tokens)))
            observe({"status": "completed", "usage": {"input_tokens": 2000, "output_tokens": 100}})
            return "OFFLINE FIXTURE: use the available ingredients."
        return generate
    report = evaluation.run(suite, "fake", tmp_path / "evidence", factory)
    # Fixed clarification turns are responses, not paid API calls.
    expected_calls = 4 if suite == "pilot" else 14
    assert len(calls) == expected_calls
    assert report["attempted_calls"] == expected_calls
    assert report["attempted_responses"] == count
    assert sum(r["response_source"] == "clinical_gate" for r in report["results"]) == count - expected_calls
    assert all(r["estimated_usd"] == 0 for r in report["results"] if not r["model_called"])
    assert report["unknown_cost_calls"] == 0
    assert len({str(c[2]["instructions"]) for c in calls}) == 1
    assert all(c[2]["max_output_tokens"] == 2048 for c in calls)
    assert all(c[1] == ("low" if c[0] == "gpt-5-mini" else "") for c in calls)
    assert all(all(v is None for v in r["scores"].values()) for r in report["results"])
    assert all(r["hard_fail"] is None for r in report["results"])


def test_access_failure_stops_spending(tmp_path):
    def factory(key, model, reasoning, observe):
        def generate(instructions, messages, max_output_tokens):
            observe({"http_status": 401})
            raise RuntimeError("fixture")
        return generate
    report = evaluation.run("full", "fake", tmp_path / "evidence", factory)
    assert report["attempted_calls"] == 1
    assert report["unknown_cost_calls"] == 1


def test_configurable_output_budget():
    for invalid in (0, 127, 2049):
        with pytest.raises(ValueError):
            KitchenCoach(lambda **kwargs: "fixture", max_output_tokens=invalid)
    assert KitchenCoach(lambda **kwargs: "fixture", max_output_tokens=2048)

@pytest.mark.parametrize("code,param,expected", [
    ("unsupported_parameter", "store", "unsupported_parameter"),
    ("secret-key-example", "secret-key-example", "unrecognized"),
])
def test_error_metadata_never_records_secrets(monkeypatch, code, param, expected):
    import json
    import requests
    from kitchen_coach import OpenAIResponses, CoachUnavailable
    class Response:
        status_code = 400
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def iter_content(self, size):
            yield json.dumps({"error": {"code": code, "type": "invalid_request_error",
                "param": param, "message": "secret-key-example private content"},
                "extra": "secret-key-example"}).encode()
    monkeypatch.setattr(requests, "post", lambda *a, **kw: Response())
    metadata = {}
    with pytest.raises(CoachUnavailable):
        OpenAIResponses("secret-key-example", "gpt-4.1-mini", observe=metadata.update)(
            "private instructions", [], 700)
    assert metadata["error_code"] == expected
    assert metadata["http_status"] == 400
    assert "secret-key-example" not in json.dumps(metadata)
    assert "private" not in json.dumps(metadata)


def test_hidden_key_input_rejects_paste_control_characters():
    from run_coach_pilot import valid_key_entry
    assert valid_key_entry("sk-" + "example" * 8)
    for invalid in ("", chr(22), "sk-" + chr(22) + "x" * 40,
                    "sk-" + "x" * 40 + " ", "sk-" + "x" * 40 + chr(10),
                    "wrong-prefix" + "x" * 40):
        assert not valid_key_entry(invalid)
