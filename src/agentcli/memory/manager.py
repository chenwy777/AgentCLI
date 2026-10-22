from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(slots=True)
class MemoryEntry:
    id: int
    scope: str
    content: str
    created_at: str


class MemoryManager:
    def __init__(self, db_path: str | Path, scope: str):
        self.db_path = Path(db_path).expanduser()
        self.scope = scope
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def save(self, content: str) -> int:
        created_at = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "insert into memories(scope, content, created_at) values (?, ?, ?)",
                (self.scope, content.strip(), created_at),
            )
            return int(cursor.lastrowid)

    def list(self, limit: int = 20) -> list[MemoryEntry]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                select id, scope, content, created_at
                from memories
                where scope = ?
                order by id desc
                limit ?
                """,
                (self.scope, limit),
            ).fetchall()
        return [MemoryEntry(*row) for row in rows]

    def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        terms = [term for term in query.lower().split() if term]
        if not terms:
            return self.list(limit)
        with self._connect() as conn:
            rows = conn.execute(
                """
                select id, scope, content, created_at
                from memories
                where scope = ?
                order by id desc
                limit 200
                """,
                (self.scope,),
            ).fetchall()
        matches = []
        for row in rows:
            content = str(row[2]).lower()
            if all(term in content for term in terms):
                matches.append(MemoryEntry(*row))
            if len(matches) >= limit:
                break
        return matches

    def clear(self) -> int:
        with self._connect() as conn:
            cursor = conn.execute("delete from memories where scope = ?", (self.scope,))
            return int(cursor.rowcount)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                create table if not exists memories (
                    id integer primary key autoincrement,
                    scope text not null,
                    content text not null,
                    created_at text not null
                )
                """
            )
            conn.execute("create index if not exists idx_memories_scope on memories(scope, id)")

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path)
        try:
            with connection:
                yield connection
        finally:
            connection.close()
