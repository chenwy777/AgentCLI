from __future__ import annotations

import sqlite3

import pytest

from agentcli.runtime import DurableTaskManager


def test_durable_task_lifecycle(tmp_path):
    manager = DurableTaskManager(tmp_path / "tasks.db")
    task_id = manager.add("do work")

    task = manager.claim_next()
    assert task is not None
    assert task.id == task_id
    assert task.status == "running"

    manager.complete(task_id, "done")
    completed = manager.get(task_id)
    assert completed is not None
    assert completed.status == "completed"
    assert completed.result == "done"


def test_durable_task_cancel(tmp_path):
    manager = DurableTaskManager(tmp_path / "tasks.db")
    task_id = manager.add("do work")

    assert manager.cancel(task_id)
    assert manager.get(task_id).status == "canceled"  # type: ignore[union-attr]


def test_durable_task_connections_are_closed(tmp_path, monkeypatch):
    connections: list[sqlite3.Connection] = []
    original_connect = sqlite3.connect

    def tracking_connect(*args, **kwargs):
        connection = original_connect(*args, **kwargs)
        connections.append(connection)
        return connection

    monkeypatch.setattr(sqlite3, "connect", tracking_connect)
    manager = DurableTaskManager(tmp_path / "tasks.db")
    task_id = manager.add("do work")
    assert manager.get(task_id) is not None

    assert connections
    for connection in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            connection.execute("select 1")
