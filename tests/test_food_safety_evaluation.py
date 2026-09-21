"""Test evidence preservation and exact authorized evaluation sequence."""
import json
from pathlib import Path
from evaluate_coach import run
from evaluate_guarded import food_safety_scenarios, remaining_scenarios
from kitchen_coach import KitchenCoach
from test_food_safety import P
import pytest

def test_eight_responses_chicken_failure_first():
    selected = food_safety_scenarios()
    assert selected[0]["id"] == "approval-request"
    assert sum(1 + bool(c.get("follow_up")) for c in selected) == 8
    assert {c["id"] for c in selected[1:]} == {
        "caribbean-sodium", "mixed-cuisine", "limited-equipment",
        "household-dislike", "missing-ingredient"}

def test_interception_is_paid_and_recorded_not_model_success(tmp_path):
    calls = []
    draft = "Rinse the chicken and pat dry."
    def factory(*args):
        def generate(*args):
            calls.append(1)
            return draft
        return generate
    report = run("food-safety-recheck", "", tmp_path / "output", factory,
                 models=["gpt-4.1-mini"], scenarios=food_safety_scenarios(),
                 review=lambda row: False)
    row = report["results"][0]
    assert row["blocked_draft"] == draft
    assert row["answer"] != draft
    assert row["response_source"] == "food_safety_gate"
    assert row["model_called"] is True
    assert report["attempted_calls"] == len(calls) == 1
    assert report["stopped_early"]
    assert row["evidence"] == "UNSCORED"
    assert report["food_safety_version"]

@pytest.mark.parametrize("draft", [
 "Cook chicken for ten minutes then serve.",
 "Put the cooked chicken on the same raw chicken plate.",
 "Use the same knife for raw chicken and salad.",
])
def test_time_only_or_cross_contamination_cannot_escape(draft):
    r = KitchenCoach(lambda *args: draft).respond(P, [], "Cook dinner")
    assert r.source == "food_safety_gate"

def test_changed_policy_evidence_cannot_resume(tmp_path):
    path = tmp_path / "old.json"
    path.write_text(json.dumps({"food_safety_version": "old-policy"}))
    with pytest.raises(ValueError, match="food policy"):
        remaining_scenarios(path, food_safety_scenarios(), "gpt-4.1-mini")
