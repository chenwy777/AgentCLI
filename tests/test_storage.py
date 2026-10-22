from __future__ import annotations

import sqlite3

import pytest

from agentcli.memory import MemoryManager
from agentcli.rag import CodeIndex


@pytest.mark.parametrize("storage", ["memory", "code_index"])
def test_storage_commits_data_and_releases_connections(tmp_path, monkeypatch, storage):
    connections = []
    connect = sqlite3.connect

    def tracked_connect(*args, **kwargs):
        connection = connect(*args, **kwargs)
        connections.append(connection)
        return connection

    monkeypatch.setattr(sqlite3, "connect", tracked_connect)

    if storage == "memory":
        manager = MemoryManager(tmp_path / "memory.db", scope="project")
        manager.save("Prefer small, reviewed batches")
        reloaded = MemoryManager(tmp_path / "memory.db", scope="project")
        assert reloaded.search("reviewed")[0].content == "Prefer small, reviewed batches"
    else:
        (tmp_path / "example.py").write_text("def configure_agent(): pass\n", encoding="utf-8")
        index = CodeIndex(tmp_path)
        assert index.rebuild("example.py") == 1
        reloaded = CodeIndex(tmp_path)
        assert reloaded.search("configure_agent")[0].line == 1

    assert connections
    for connection in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            connection.execute("SELECT 1")
