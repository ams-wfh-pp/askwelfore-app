"""The two regressions must precede the five outstanding responses."""
import pytest
from evaluate_coach import run
from evaluate_guarded import food_action_scenarios

def test_rerun_order_and_limit():
    cases = food_action_scenarios()
    assert [c["id"] for c in cases] == [
        "mixed-cuisine", "rice-rinsing-recheck", "limited-equipment",
        "household-dislike", "missing-ingredient"]
    assert sum(1 + bool(c.get("follow_up")) for c in cases) == 7
    assert "rinse the rice" in cases[1]["question"]
    assert cases[1]["profile"]["culture"] == "Jamaican / Caribbean"

@pytest.mark.parametrize("failure_index", [0, 1])
def test_failure_in_either_recheck_stops_remaining_paid_calls(tmp_path, failure_index):
    calls = []
    def factory(*args):
        def generate(*args):
            calls.append(1)
            return "Use the thyme and garlic you have for flavor."
        return generate
    reviews = []
    def review(row):
        reviews.append(row)
        return len(reviews) <= failure_index
    report = run("food-action-recheck", "", tmp_path / "out", factory,
                 models=["gpt-4.1-mini"], scenarios=food_action_scenarios(),
                 review=review, max_output_tokens=700)
    assert len(calls) == failure_index + 1
    assert report["stopped_early"]
    assert len(report["results"]) == failure_index + 1
