"""Local masked input; no key files, shell history or persistent settings."""
import sys
from datetime import datetime
from pathlib import Path
from run_coach_pilot import valid_key_entry

def normalize_entry(value):
    # Notepad selections often include a final newline; never alter internal text.
    return value.strip() if value else ""

def main():
    import tkinter as tk
    from tkinter import messagebox, simpledialog
    if sys.argv[1:] not in ([], ["--pilot"]):
        raise SystemExit("Unknown option; no API calls made.")
    pilot = sys.argv[1:] == ["--pilot"]
    root = tk.Tk()
    root.withdraw()
    key = ""
    try:
        key = normalize_entry(simpledialog.askstring(
            "AskWelFore - private key entry",
            "Paste your OpenAI API key here using Ctrl+V.\n"
            "Characters are hidden. The key is not saved.\n"
            "This first step checks the text only.",
            show="*", parent=root))
        if not key:
            messagebox.showinfo("Cancelled", "No key entered. No API calls made.", parent=root)
            return
        if not valid_key_entry(key):
            messagebox.showerror("Input needs checking",
                "The pasted text is not in the expected format.\n"
                "No API calls were made and the key was not saved.\n"
                "Copy only the full key from Notepad, without quotes.", parent=root)
            return
        if not pilot:
            messagebox.showinfo("Local check passed",
                "The input format passed. No API calls were made.\n"
                "The key was not saved. Account access is not yet verified.", parent=root)
            return
        if not messagebox.askyesno("Approve six-call pilot",
                "Run the pilot now? At most 6 paid API requests, no retries.\n"
                "Allow up to $0.10 in API usage. No purchase, merge or deployment.\n"
                "Only fictional cooking cases are sent.\n"
                "Click No to cancel without making any requests.", parent=root):
            return
        # Same tested pilot runner; no secrets written to environment or output.
        from evaluate_coach import run, ROOT
        output = ROOT / "eval-results" / datetime.now().strftime("%Y%m%d-%H%M%S")
        print("Pilot running. Please wait; do not launch it again.", flush=True)
        try:
            report = run("pilot", key, output)
        except Exception:
            messagebox.showerror("Pilot stopped",
                "The pilot stopped. Do not retry yet. Tell Codex so it can inspect "
                "any saved evidence. The key has not been saved.", parent=root)
            return
        failed = any(r["application_status"] != "ok" for r in report["results"])
        messagebox.showinfo("Pilot stopped" if failed else "Pilot finished",
            "The pilot " + ("stopped with a failed request." if failed else "finished.") +
            "\nTell Codex it finished; it can read the local results.\n"
            "The key has not been saved.", parent=root)
    finally:
        key = ""
        root.destroy()

if __name__ == "__main__":
    main()
