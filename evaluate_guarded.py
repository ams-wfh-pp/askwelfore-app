"""Operator-reviewed, sequential evaluation. Credentials stay in local memory."""
import argparse
import hashlib
import json
import sys
from datetime import datetime
from evaluate_coach import ROOT, DIMENSIONS, cases, run
from coach_key_window import normalize_entry
from run_coach_pilot import valid_key_entry

def scenarios():
    base = cases("full")
    extra = json.loads((ROOT / "tests/coach_safety_scenarios.json").read_text(encoding="utf-8"))
    by_id = {case["id"]: case for case in base + extra}
    order = ["conflicting-guidance", "unclear-renal-electrolytes",
             "diabetes-medication-unclear", "allergy-substitution",
             "new-allergy-follow-up", "approval-request", "caribbean-sodium",
             "mixed-cuisine", "limited-equipment", "household-dislike", "missing-ingredient"]
    return [by_id[name] for name in order]

def review_response(row):
    digest = hashlib.sha256(row["answer"].encode()).hexdigest()
    print("REVIEW_REQUIRED " + json.dumps({"answer_sha256": digest, **row}), flush=True)
    # Reviewed by the operator, not by an automated keyword pass or a paid judge.
    # Invalid input / EOF is a permanent stop for this run.
    try:
        decision = json.loads(sys.stdin.readline())
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

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    # This selection affects the evaluation only; the app model remains configurable.
    parser.add_argument("--model", choices=["gpt-4.1-mini"], default="gpt-4.1-mini")
    args = parser.parse_args()
    selected = scenarios()
    count = sum(1 + bool(case.get("follow_up")) for case in selected)
    print(f"Guarded evaluation: at most {count} calls; model {args.model}; 700 output tokens; no retries.", flush=True)
    if not args.live:
        print("Dry run. No key requested or API called.", flush=True)
        return
    import tkinter as tk
    from tkinter import simpledialog
    root = tk.Tk()
    root.withdraw()
    key = ""
    try:
        key = normalize_entry(simpledialog.askstring(
            "AskWelFore - revised evaluation",
            "Paste your OpenAI key using Ctrl+V. It stays hidden and is not saved.\n"
            "You authorized this revised GPT-4.1 mini evaluation.\n"
            "Click OK to start; each answer pauses for Codex review.\n"
            "Cancel sends no requests.",
            show="*", parent=root))
    finally:
        root.destroy()
    if not valid_key_entry(key):
        key = ""
        print("Cancelled or invalid key input. No API requests made.", flush=True)
        return
    output = ROOT / "eval-results" / (datetime.now().strftime("%Y%m%d-%H%M%S") + "-guarded")
    try:
        report = run("revised-safety", key, output, models=[args.model],
                     scenarios=selected, review=review_response, max_output_tokens=700)
        print("EVALUATION_STOPPED" if report["stopped_early"] else "EVALUATION_FINISHED", flush=True)
        print("Evidence: " + str(output), flush=True)
    except Exception:
        print("Evaluation stopped unexpectedly. Inspect saved evidence before any retry.", flush=True)
    finally:
        key = ""

if __name__ == "__main__":
    main()
