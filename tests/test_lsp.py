from __future__ import annotations

from agentcli.lsp import diagnose_file


def test_python_diagnostics(tmp_path):
    path = tmp_path / "bad.py"
    path.write_text("def nope(:\n", encoding="utf-8")

    diagnostics = diagnose_file(path)

    assert diagnostics
    assert "SyntaxError" in diagnostics[0]
