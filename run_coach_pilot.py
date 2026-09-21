"""Secure local launcher for the six-call pilot; never stores the key."""
import getpass
import os
from evaluate_coach import main

if __name__ == "__main__":
    print("Paid pilot: at most 6 API calls, no retries. Allow up to $0.10 in API usage.")
    if input("Type APPROVE PILOT to continue: ").strip() != "APPROVE PILOT":
        raise SystemExit("Cancelled; no API calls made.")
    key = getpass.getpass("OpenAI project API key (hidden): ").strip()
    if not key:
        raise SystemExit("No key; no API calls made.")
    os.environ["COACH_EVAL_APPROVED"] = "YES"
    os.environ["COACH_EVAL_API_KEY"] = key
    try:
        main(["--suite", "pilot", "--live"])
    finally:
        os.environ.pop("COACH_EVAL_API_KEY", None)
        os.environ.pop("COACH_EVAL_APPROVED", None)
        key = ""
