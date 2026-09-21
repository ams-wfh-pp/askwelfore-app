"""Local review mailbox. Contains fictional evidence and decisions, never keys."""
import json
import time

def wait_review(output, row, digest, timeout=1200, clock=time.monotonic, sleep=time.sleep):
    decision_name = "decision-" + row["scenario"] + "-" + str(row["turn"]) + ".json"
    decision_path = output / decision_name
    pending = output / "review-pending.json"
    pending.write_text(json.dumps({
        "scenario": row["scenario"], "turn": row["turn"],
        "answer_sha256": digest, "decision_file": decision_name,
    }, indent=2), encoding="utf-8")
    deadline = clock() + timeout
    try:
        while clock() < deadline:
            if decision_path.exists():
                return json.loads(decision_path.read_text(encoding="utf-8"))
            sleep(0.2)
        return {}  # No review: stop, never approve automatically.
    finally:
        pending.unlink(missing_ok=True)
