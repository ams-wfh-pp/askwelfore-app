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
            assert len(calls) == len(reviews)
            calls.append(messages)
            return "OFFLINE FIXTURE ONLY"
        return generate
    def review(row):
        reviews.append(row)
        return True
    report = run("revised", "fake", tmp_path / "evidence", factory,
                 models=["gpt-4.1-mini"], scenarios=guarded.scenarios(),
                 review=review, max_output_tokens=700)
    assert len(calls) == len(reviews) == 16
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
