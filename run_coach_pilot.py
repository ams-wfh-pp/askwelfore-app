"""Secure local launcher for the six-call pilot; never stores the key."""
import getpass
import os
import sys
from evaluate_coach import main

def valid_key_entry(value):
    return value.startswith("sk-") and len(value) >= 20 and all(33 <= ord(c) <= 126 for c in value)


if __name__ == "__main__":
    check_only = sys.argv[1:] == ["--check-key"]
    if sys.argv[1:] and not check_only:
        raise SystemExit("Unknown option; no API calls made.")
    if check_only:
        print("Local input check only. No API requests will be made.")
    else:
        print("Paid pilot: at most 6 API calls, no retries. Allow up to $0.10 in API usage.")
        if input("Type APPROVE PILOT to continue: ").strip() != "APPROVE PILOT":
            raise SystemExit("Cancelled; no API calls made.")
    key = getpass.getpass("OpenAI project API key (hidden): ")
    if not key:
        raise SystemExit("No key; no API calls made.")
    if not valid_key_entry(key):
        key = ""
        raise SystemExit("Key input format was not valid. No API request was sent. The key was not saved or displayed.")
    if check_only:
        key = ""
        raise SystemExit("Input format passed. Key validity and account access have NOT been checked. No API calls made.")
    os.environ["COACH_EVAL_APPROVED"] = "YES"
    os.environ["COACH_EVAL_API_KEY"] = key
    try:
        main(["--suite", "pilot", "--live"])
    finally:
        os.environ.pop("COACH_EVAL_API_KEY", None)
        os.environ.pop("COACH_EVAL_APPROVED", None)
        key = ""
