import sys
from types import SimpleNamespace
import pytest
import coach_key_window as window

@pytest.mark.parametrize("args,approval,expected_calls", [
    ([], False, 0), (["--pilot"], False, 0), (["--pilot"], True, 1)
])
def test_window_requires_explicit_paid_confirmation(monkeypatch, tmp_path, args, approval, expected_calls):
    import evaluate_coach
    calls, notices = [], []
    key = "sk-" + "fixture" * 8
    root = SimpleNamespace(withdraw=lambda: None, destroy=lambda: None)
    def askstring(*a, **kw):
        assert kw["show"] == "*"
        return "  " + key + "\n"
    dialogs = SimpleNamespace(askstring=askstring)
    boxes = SimpleNamespace(
        showinfo=lambda *a, **kw: notices.append(str(a)),
        showerror=lambda *a, **kw: notices.append(str(a)),
        askyesno=lambda *a, **kw: approval)
    monkeypatch.setitem(sys.modules, "tkinter", SimpleNamespace(
        Tk=lambda: root, messagebox=boxes, simpledialog=dialogs))
    monkeypatch.setattr(sys, "argv", ["coach_key_window.py"] + args)
    monkeypatch.setattr(evaluate_coach, "ROOT", tmp_path)
    def run(suite, supplied_key, output):
        assert supplied_key == key
        assert suite == "pilot"
        calls.append(suite)
        return {"results": [{"application_status": "ok"}]}
    monkeypatch.setattr(evaluate_coach, "run", run)
    window.main()
    assert len(calls) == expected_calls
    assert all(key not in notice for notice in notices)
