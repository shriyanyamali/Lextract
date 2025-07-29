import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

import glob
import subprocess
import pytest

import run_pipeline


def test_safe_run_missing_paths(monkeypatch, capsys):

    monkeypatch.setattr(os.path, "exists", lambda path: False)
    run_pipeline.safe_run(
        ["python", "script.py"],
        description="step1",
        input_paths=["foo.txt", "bar.txt"],
    )

    captured = capsys.readouterr().out
    assert "Warning: missing foo.txt, bar.txt; skipping step1." in captured


def test_safe_run_missing_default_description(monkeypatch, capsys):
    # If description is None, it should fall back to cmd[1]
    monkeypatch.setattr(os.path, "exists", lambda path: False)
    run_pipeline.safe_run(["python", "myscript.py"], input_paths=["x"])
    captured = capsys.readouterr().out
    assert "Warning: missing x; skipping myscript.py." in captured


def test_safe_run_success(monkeypatch, capsys):
    # Simulate all inputs exist and subprocess.run succeeds
    monkeypatch.setattr(os.path, "exists", lambda path: True)

    calls = []
    def fake_run(cmd, check):
        calls.append((cmd, check))

    monkeypatch.setattr(subprocess, "run", fake_run)

    run_pipeline.safe_run([sys.executable, "hello.py", "--opt"], description=None)
    out = capsys.readouterr().out

    assert out.startswith("Running: ")
    assert calls == [([sys.executable, "hello.py", "--opt"], True)]


def test_safe_run_file_not_found(monkeypatch, capsys):
    monkeypatch.setattr(os.path, "exists", lambda path: True)

    def fake_run(cmd, check):
        e = FileNotFoundError()
        e.filename = cmd[1]
        raise e

    monkeypatch.setattr(subprocess, "run", fake_run)

    run_pipeline.safe_run(
        ["python", "no_such_script.py"],
        description="fetch"
    )
    captured = capsys.readouterr().out
    assert "Warning: file or script not found (no_such_script.py); skipping fetch." in captured


def test_safe_run_called_process_error(monkeypatch, capsys):
    monkeypatch.setattr(os.path, "exists", lambda path: True)

    def fake_run(cmd, check):
        raise subprocess.CalledProcessError(returncode=5, cmd=cmd)

    monkeypatch.setattr(subprocess, "run", fake_run)

    run_pipeline.safe_run(["cmd"], description="desc2")
    captured = capsys.readouterr().out
    assert "Warning: step desc2 failed (exit 5); continuing." in captured


def test_main_counts(monkeypatch, capsys):

    monkeypatch.setattr(run_pipeline, "safe_run", lambda *a, **k: None)

    def fake_glob(pattern):
        if "pdf_texts_79_batch_" in pattern:
            return ["b79_1.txt", "b79_2.txt", "b79_3.txt"]
        if "pdf_texts_80_batch_" in pattern:
            return ["b80_1.txt", "b80_2.txt"]
        if "extract-sections_batch_" in pattern:
            return ["s1.txt", "s2.txt", "s3.txt", "s4.txt", "s5.txt"]
        if pattern.endswith(os.path.join("json", "*.json")):
            return ["j1.json", "j2.json", "j3.json", "j4.json"]
        return []

    monkeypatch.setattr(glob, "glob", fake_glob)

    monkeypatch.setattr(os.path, "exists", lambda path: path.endswith(os.path.join("data", "output.json")))

    run_pipeline.main()
    out = capsys.readouterr().out

    assert "- 3 x 79 batches" in out
    assert "- 2 x 80 batches" in out
    assert "- 5 section files" in out
    assert "- 4 JSON files" in out
    assert "- 1 merged file" in out
