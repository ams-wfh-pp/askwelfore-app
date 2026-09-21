"""Explicit opt-in evaluation of fictional cases. Dry-run is the default."""
import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from kitchen_coach import INSTRUCTIONS, KitchenCoach, OpenAIResponses
from clinical_gate import VERSION as GATE_VERSION

ROOT = Path(__file__).parent
MODEL_SETTINGS = {
    "gpt-4.1-mini": {"reasoning": "", "input": .40, "cached": .10, "output": 1.60},
    "gpt-5-mini": {"reasoning": "low", "input": .25, "cached": .025, "output": 2.00},
}
DEFAULT_PROFILE = {
    "household": "Two adults; one shared meal", "culture": "Caribbean",
    "restrictions": "None", "guidance": "Reduce sodium", "source": "My doctor",
    "ingredients": "Chicken, rice, thyme, garlic", "constraints": "30 minutes; stove; beginner",
}
DIMENSIONS = [
    "trusted_guidance", "culture_flavor", "familiar_meal", "allergies_restrictions",
    "household_practicality", "no_clinical_prescribing", "cooking_usefulness",
    "concise_voice_ready", "follow_up_context",
]


def cases(suite):
    all_cases = json.loads((ROOT / "tests/coach_scenarios.json").read_text(encoding="utf-8"))
    return all_cases if suite == "full" else [
        case for case in all_cases if case["id"] in ("missing-ingredient", "conflicting-guidance")
    ]


def estimate_cost(usage, model):
    if not usage or "input_tokens" not in usage or "output_tokens" not in usage:
        return None
    rate = MODEL_SETTINGS[model]
    cached = usage.get("input_tokens_details", {}).get("cached_tokens", 0)
    return round(((usage["input_tokens"] - cached) * rate["input"]
                  + cached * rate["cached"] + usage["output_tokens"] * rate["output"]) / 1e6, 8)


def run(suite, key, output, adapter_factory=OpenAIResponses, *,
        models=None, scenarios=None, review=None, max_output_tokens=2048):
    models = list(MODEL_SETTINGS) if models is None else list(models)
    if not models or any(model not in MODEL_SETTINGS for model in models):
        raise ValueError("Unsupported evaluation model")
    KitchenCoach(lambda *args: "", max_output_tokens=max_output_tokens)
    scenarios = cases(suite) if scenarios is None else scenarios
    total = len(models) * sum(1 + bool(case.get("follow_up")) for case in scenarios)
    # One run only, no retries or auto-fallback. Do not overwrite previous evidence.
    output.mkdir(parents=True, exist_ok=False)
    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "suite": suite, "gate_version": GATE_VERSION, "prompt_sha256": hashlib.sha256(INSTRUCTIONS.encode()).hexdigest(),
        "scenario_sha256": hashlib.sha256(json.dumps(scenarios, sort_keys=True).encode()).hexdigest(),
        "max_calls": total, "max_output_tokens": max_output_tokens,
        "models": {model: MODEL_SETTINGS[model] for model in models}, "rubric": DIMENSIONS, "results": [],
        "review_required": review is not None, "stopped_early": False,
        "decision": "NOT SCORED. No winner until actual outputs are reviewed.",
    }
    (output / "prompt.txt").write_text(INSTRUCTIONS, encoding="utf-8")
    (output / "scenarios.json").write_text(json.dumps(scenarios, indent=2), encoding="utf-8")
    stop = False
    attempted = 0
    for scenario_index, case in enumerate(scenarios):
        # Alternate which model is first to reduce fixed ordering bias.
        names = list(models)
        if scenario_index % 2:
            names.reverse()
        for model in names:
            if stop:
                break
            profile = {**DEFAULT_PROFILE, **case["profile"]}
            history = []
            questions = [case["question"]] + ([case["follow_up"]] if case.get("follow_up") else [])
            for turn, question in enumerate(questions, 1):
                telemetry = {}
                adapter = adapter_factory(key, model, MODEL_SETTINGS[model]["reasoning"], telemetry.update)
                generation_called = False
                def generate(*args):
                    nonlocal generation_called
                    generation_called = True
                    return adapter(*args)
                service = KitchenCoach(generate, max_output_tokens=max_output_tokens)
                row = {"scenario": case["id"], "model_requested": model, "turn": turn,
                       "profile": profile, "prior_messages": list(history), "question": question,
                       "expectation": case["expectation"], "answer": None,
                       "scores": {dimension: None for dimension in DIMENSIONS},
                       "hard_fail": None, "review_notes": "",
                       "evidence": "UNSCORED"}
                start = time.monotonic()
                attempted += 1
                try:
                    reply = service.respond(profile, history, question)
                    answer = reply.text
                    row.update(answer=answer, word_count=len(answer.split()), application_status="ok",
                               response_source=reply.source, safety_reason=reply.safety_reason)
                    history.extend([{"role": "user", "content": question},
                                    {"role": "assistant", "content": answer}])
                except Exception:
                    row["application_status"] = "failed"
                    # Do not automatically spend more after access/model/funding failures.
                    if telemetry.get("http_status") in (400, 401, 403, 404, 429):
                        stop = True
                row["elapsed_seconds"] = round(time.monotonic() - start, 3)
                row["model_called"] = generation_called
                row["provider"] = telemetry if generation_called else {"status": "not_called"}
                row["estimated_usd"] = estimate_cost(telemetry.get("usage"), model) if generation_called else 0.0
                report["results"].append(row)
                report["attempted_responses"] = attempted
                report["attempted_calls"] = sum(r["model_called"] for r in report["results"])
                report["known_estimated_usd"] = round(sum(
                    r["estimated_usd"] or 0 for r in report["results"]), 8)
                report["unknown_cost_calls"] = sum(
                    r["estimated_usd"] is None for r in report["results"])
                (output / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
                print(f"{case['id']} / {model} / turn {turn}: {row['application_status']}", flush=True)
                if review is not None:
                    # No next call until the operator has read this exact response.
                    # Review errors, EOF and any explicit stop fail closed.
                    try:
                        continue_run = row["application_status"] == "ok" and review(row) is True
                    except Exception:
                        continue_run = False
                    if not continue_run:
                        stop = True
                        report["stopped_early"] = True
                        report["decision"] = "STOPPED. Review the last response; do not resume automatically."
                    (output / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
                if stop or row["application_status"] != "ok":
                    break  # No fabricated follow-up context or calls after a stop.
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=["pilot", "full"], default="pilot")
    parser.add_argument("--live", action="store_true", help="Makes paid API calls; requires explicit approval flag.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    count = 2 * sum(1 + bool(case.get("follow_up")) for case in cases(args.suite))
    print(f"{args.suite}: at most {count} API calls, 2,048 output tokens per call, no retries.")
    print("Same coaching instructions and scenarios. GPT-5 mini: low reasoning; GPT-4.1 mini: no reasoning parameter.")
    if not args.live:
        print("DRY RUN. No key accessed, API called, or model quality score produced.")
        return 0
    if os.getenv("COACH_EVAL_APPROVED") != "YES":
        parser.error("Paid evaluation needs COACH_EVAL_APPROVED=YES after user approval.")
    key = os.getenv("COACH_EVAL_API_KEY")
    if not key:
        parser.error("Set COACH_EVAL_API_KEY securely. Do not paste it into chat or commit it.")
    output = args.output or ROOT / "eval-results" / datetime.now().strftime("%Y%m%d-%H%M%S")
    run(args.suite, key, output)
    print(f"Evidence saved locally to {output}. Review all dimensions before choosing a model.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
