"""Operator-reviewed, sequential evaluation. Credentials stay in local memory."""
import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from evaluate_coach import ROOT, DIMENSIONS, cases, run
from coach_key_window import normalize_entry
from run_coach_pilot import valid_key_entry

def scenarios():
    base = cases("full")
    extra = json.loads((ROOT / "tests/coach_safety_scenarios.json").read_text(encoding="utf-8"))
    by_id = {case["id"]: case for case in base + extra}
    order = ["unclear-renal-electrolytes", "conflicting-guidance",
             "diabetes-medication-unclear", "allergy-substitution",
             "new-allergy-follow-up", "approval-request", "caribbean-sodium",
             "mixed-cuisine", "limited-equipment", "household-dislike", "missing-ingredient"]
    return [by_id[name] for name in order]

def remaining_scenarios(previous, selected, model):
    from kitchen_coach import INSTRUCTIONS
    report = json.loads(previous.read_text(encoding="utf-8"))
    from clinical_gate import VERSION
    if report.get("gate_version") != VERSION:
        raise ValueError("Cannot resume across clinical gate changes")
    if report["prompt_sha256"] != hashlib.sha256(INSTRUCTIONS.encode()).hexdigest():
        raise ValueError("Cannot resume after instructions changed")
    if report["scenario_sha256"] != hashlib.sha256(json.dumps(selected, sort_keys=True).encode()).hexdigest():
        raise ValueError("Cannot resume changed scenarios")
    rows = report["results"]
    if not rows or any(r["model_requested"] != model or r["application_status"] != "ok"
                       or r.get("hard_fail") is not False or r.get("evidence") != "OPERATOR_REVIEWED"
                       for r in rows):
        raise ValueError("Previous responses must be reviewed without a hard failure")
    completed = set()
    for case in selected:
        matching = [r for r in rows if r["scenario"] == case["id"]]
        if matching:
            expected = 1 + bool(case.get("follow_up"))
            if [r["turn"] for r in matching] != list(range(1, expected + 1)):
                raise ValueError("Do not resume an incomplete scenario")
            completed.add(case["id"])
    if any(r["scenario"] not in completed for r in rows):
        raise ValueError("Unknown previous scenario")
    return [case for case in selected if case["id"] not in completed]

def review_response(row, decision_reader=None):
    digest = hashlib.sha256(row["answer"].encode()).hexdigest()
    print("REVIEW_REQUIRED " + json.dumps({"answer_sha256": digest, **row}), flush=True)
    # Reviewed by the operator, not by an automated keyword pass or a paid judge.
    # Invalid input / EOF is a permanent stop for this run.
    try:
        decision = decision_reader(row, digest) if decision_reader else json.loads(sys.stdin.readline())
        scores = decision["scores"]
        if decision.get("answer_sha256") != digest:
            return False
        if set(scores) != set(DIMENSIONS) or any(
                v is not None and (type(v) is not int or not 0 <= v <= 3) for v in scores.values()):
            return False
        if type(decision.get("hard_fail")) is not bool or not decision.get("notes"):
            return False
        row.update(scores=scores, hard_fail=decision["hard_fail"],
                   review_notes=decision["notes"], evidence="OPERATOR_REVIEWED")
        return decision.get("decision") == "continue" and decision["hard_fail"] is False
    except Exception:
        return False

class DeferredProvider:
    """Do not request credentials for fixed gate replies."""
    def __init__(self, get_key, adapter_factory=None):
        from kitchen_coach import OpenAIResponses
        self.get_key = get_key
        self.adapter_factory = adapter_factory or OpenAIResponses
        self.key = ""

    def factory(self, unused_key, model, reasoning, observe):
        def generate(*args):
            if not self.key:
                self.key = normalize_entry(self.get_key())
                if not valid_key_entry(self.key):
                    self.clear()
                    raise ValueError("Cancelled or invalid key entry")
            return self.adapter_factory(self.key, model, reasoning, observe)(*args)
        return generate

    def clear(self):
        self.key = ""

def prompt_key():
    import tkinter as tk
    from tkinter import simpledialog
    root = tk.Tk()
    root.withdraw()
    try:
        return simpledialog.askstring(
            "AskWelFore - remaining evaluation",
            "The fixed safety checks passed. Paste your OpenAI key using Ctrl+V.\n"
            "It is hidden and not saved.\n"
            "Click OK to continue the evaluation you authorized.\n"
            "Each response pauses for Codex review. Cancel sends no request.",
            show="*", parent=root)
    finally:
        root.destroy()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    # This selection affects the evaluation only; the app model remains configurable.
    parser.add_argument("--model", choices=["gpt-4.1-mini"], default="gpt-4.1-mini")
    parser.add_argument("--resume-reviewed", type=Path)
    args = parser.parse_args()
    selected = scenarios()
    if args.resume_reviewed:
        selected = remaining_scenarios(args.resume_reviewed, selected, args.model)
    count = sum(1 + bool(case.get("follow_up")) for case in selected)
    print(f"Guarded evaluation: at most {count} responses (gated replies make no API call); model {args.model}; 700 output tokens; no retries.", flush=True)
    if not args.live:
        print("Dry run. No key requested or API called.", flush=True)
        return
    deferred = DeferredProvider(prompt_key)
    output = ROOT / "eval-results" / (datetime.now().strftime("%Y%m%d-%H%M%S") + "-guarded")
    from evaluation_review import wait_review
    try:
        report = run("revised-safety", "", output, adapter_factory=deferred.factory, models=[args.model],
                     scenarios=selected, review=lambda row: review_response(row, lambda item, digest: wait_review(output, item, digest)), max_output_tokens=700)
        print("EVALUATION_STOPPED" if report["stopped_early"] else "EVALUATION_FINISHED", flush=True)
        print("Evidence: " + str(output), flush=True)
    except Exception:
        print("Evaluation stopped unexpectedly. Inspect saved evidence before any retry.", flush=True)
    finally:
        deferred.clear()

if __name__ == "__main__":
    main()
