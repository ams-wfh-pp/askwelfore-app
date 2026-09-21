"""Offline review-gate tests; these do not establish live model safety."""
import hashlib
import io
import json
import pytest
import evaluate_guarded as guarded
from evaluate_coach import DIMENSIONS, run
from kitchen_coach import INSTRUCTIONS

@pytest.mark.parametrize("decision", ["stop", "eof", "error"])
def test_no_call_after_unapproved_response(tmp_path, decision):
    calls = []
    def factory(*args):
        def generate(instructions, messages, limit):
            assert instructions == INSTRUCTIONS
            assert limit == 700
            calls.append(messages)
            return "OFFLINE FIXTURE ONLY"
        return generate
    def review(row):
        if decision == "error":
            raise RuntimeError("review unavailable")
        return False
    report = run("full", "fake", tmp_path / "evidence", factory,
                 models=["gpt-4.1-mini"], review=review, max_output_tokens=700)
    assert len(calls) == 1
    assert report["stopped_early"]

def test_all_calls_require_review_before_next(tmp_path):
    calls, reviews = [], []
    def factory(key, model, reasoning, observe):
        assert model == "gpt-4.1-mini" and reasoning == ""
        def generate(instructions, messages, limit):
            assert not calls or reviews[-1]["evidence"] == "fixture_reviewed"
            calls.append(messages)
            return "OFFLINE FIXTURE ONLY"
        return generate
    def review(row):
        row["evidence"] = "fixture_reviewed"
        reviews.append(row)
        return True
    report = run("revised", "fake", tmp_path / "evidence", factory,
                 models=["gpt-4.1-mini"], scenarios=guarded.scenarios(),
                 review=review, max_output_tokens=700)
    assert len(calls) == 8
    assert len(reviews) == 16
    assert report["attempted_calls"] == 8
    assert not report["stopped_early"]

@pytest.mark.parametrize("change", [
    {"decision": "stop"}, {"hard_fail": True},
    {"answer_sha256": "wrong response"}, {"scores": {}}, {"hard_fail": "false"}
])
def test_review_rejects_failure_or_mismatched_response(monkeypatch, change):
    row = {"answer": "Fixture"}
    decision = {"answer_sha256": hashlib.sha256(b"Fixture").hexdigest(),
                "decision": "continue", "hard_fail": False, "notes": "Offline fixture",
                "scores": {name: None for name in DIMENSIONS}}
    decision.update(change)
    monkeypatch.setattr(guarded.sys, "stdin", io.StringIO(json.dumps(decision) + "\n"))
    assert guarded.review_response(row) is False

def test_api_failure_stops_before_review_and_next_call(tmp_path):
    calls = []
    def factory(*args):
        def generate(*args):
            calls.append(1)
            raise RuntimeError("fixture failure")
        return generate
    report = run("full", "fake", tmp_path / "evidence", factory,
                 models=["gpt-4.1-mini"], review=lambda row: pytest.fail("No successful answer to review"))
    assert len(calls) == 1
    assert report["stopped_early"]

def test_resume_skips_only_completed_reviewed_cases(tmp_path):
    from kitchen_coach import INSTRUCTIONS
    selected = guarded.scenarios()
    from clinical_gate import VERSION
    from food_safety import VERSION as FOOD_VERSION
    from kitchen_context import VERSION as KITCHEN_VERSION
    report = {"kitchen_context_version": KITCHEN_VERSION, "food_safety_version": FOOD_VERSION, "gate_version": VERSION, "prompt_sha256": hashlib.sha256(INSTRUCTIONS.encode()).hexdigest(),
              "scenario_sha256": hashlib.sha256(json.dumps(selected, sort_keys=True).encode()).hexdigest(),
              "results": [{"scenario": selected[0]["id"], "turn": 1,
                           "model_requested": "gpt-4.1-mini", "application_status": "ok",
                           "hard_fail": False, "evidence": "OPERATOR_REVIEWED"}]}
    report["results"].append({**report["results"][0], "turn": 2})
    path = tmp_path / "previous.json"
    path.write_text(json.dumps(report))
    assert guarded.remaining_scenarios(path, selected, "gpt-4.1-mini") == selected[1:]
    report["results"][0]["hard_fail"] = True
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError):
        guarded.remaining_scenarios(path, selected, "gpt-4.1-mini")
    report["results"][0]["hard_fail"] = None
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError):
        guarded.remaining_scenarios(path, selected, "gpt-4.1-mini")

def test_credentials_requested_only_when_generation_is_needed():
    requests = []
    def get_key():
        requests.append("key prompt")
        return "sk-" + "fixture" * 8
    def adapter(*args):
        return lambda *args: "fixture answer"
    provider = guarded.DeferredProvider(get_key, adapter)
    generate = provider.factory("", "gpt-4.1-mini", "", lambda value: None)
    assert requests == []
    assert generate("instructions", [], 700) == "fixture answer"
    assert generate("instructions", [], 700) == "fixture answer"
    assert requests == ["key prompt"]
    provider.clear()
    assert provider.key == ""

def test_file_review_timeout_never_approves(tmp_path):
    from evaluation_review import wait_review
    now = [0]
    row = {"scenario": "fixture", "turn": 1}
    def advance(seconds):
        now[0] += seconds
    assert wait_review(tmp_path, row, "abc", timeout=0.3,
                       clock=lambda: now[0], sleep=advance) == {}
    assert not (tmp_path / "review-pending.json").exists()

def test_file_review_reads_exact_decision(tmp_path):
    from evaluation_review import wait_review
    row = {"answer": "Fixture", "scenario": "fixture", "turn": 1}
    decision = {"answer_sha256": hashlib.sha256(b"Fixture").hexdigest(),
                "decision": "continue", "hard_fail": False, "notes": "Offline fixture",
                "scores": {name: None for name in DIMENSIONS}}
    (tmp_path / "decision-fixture-1.json").write_text(json.dumps(decision))
    assert guarded.review_response(row, lambda item, digest: wait_review(tmp_path, item, digest))
    assert row["hard_fail"] is False
