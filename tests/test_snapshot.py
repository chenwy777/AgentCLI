from __future__ import annotations

from agentcli.snapshot import SnapshotService


def test_snapshot_restore(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    project = tmp_path / "project"
    project.mkdir()
    file_path = project / "note.txt"
    file_path.write_text("before", encoding="utf-8")

    service = SnapshotService(project)
    first = service.create("pre-turn")
    file_path.write_text("after", encoding="utf-8")

    restored = service.restore(first.id)

    assert restored.id == first.id
    assert file_path.read_text(encoding="utf-8") == "before"
