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
    assert len(calls) == count
    assert report["attempted_calls"] == count
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
