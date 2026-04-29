# Copyright 2026 Jiacheng Ni
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ApprovalRecord:
    request_id: str
    action: str
    risk: str
    status: str
    reason: str
    metadata: dict[str, Any]


class MemoryStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.initialize()

    def close(self) -> None:
        self.conn.close()

    def initialize(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS memories (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                importance INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                channel TEXT NOT NULL,
                sender TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                risk TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS approvals (
                request_id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                risk TEXT NOT NULL,
                status TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                decided_at TEXT,
                metadata TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def set_memory(self, key: str, value: str, importance: int = 1) -> None:
        now = utcnow()
        self.conn.execute(
            """
            INSERT INTO memories(key, value, importance, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value=excluded.value,
                importance=excluded.importance,
                updated_at=excluded.updated_at
            """,
            (key, value, importance, now, now),
        )
        self.conn.commit()

    def get_memory(self, key: str) -> str | None:
        row = self.conn.execute("SELECT value FROM memories WHERE key = ?", (key,)).fetchone()
        return str(row["value"]) if row else None

    def search_memories(self, query: str, limit: int = 8) -> list[tuple[str, str]]:
        like = f"%{query}%"
        rows = self.conn.execute(
            """
            SELECT key, value
            FROM memories
            WHERE key LIKE ? OR value LIKE ?
            ORDER BY importance DESC, updated_at DESC
            LIMIT ?
            """,
            (like, like, limit),
        ).fetchall()
        return [(str(row["key"]), str(row["value"])) for row in rows]

    def memory_excerpt(self, limit: int = 12) -> str:
        rows = self.conn.execute(
            "SELECT key, value FROM memories ORDER BY importance DESC, updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return "\n".join(f"- {row['key']}: {row['value']}" for row in rows)

    def append_message(
        self,
        *,
        channel: str,
        sender: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        message_id = str(uuid4())
        self.conn.execute(
            """
            INSERT INTO messages(id, channel, sender, role, content, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                channel,
                sender,
                role,
                content,
                utcnow(),
                json.dumps(metadata or {}, ensure_ascii=False),
            ),
        )
        self.conn.commit()
        return message_id

    def create_task(
        self,
        title: str,
        *,
        risk: str = "low",
        status: str = "open",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        task_id = str(uuid4())
        now = utcnow()
        self.conn.execute(
            """
            INSERT INTO tasks(id, title, status, risk, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                title,
                status,
                risk,
                now,
                now,
                json.dumps(metadata or {}, ensure_ascii=False),
            ),
        )
        self.conn.commit()
        return task_id

    def request_approval(
        self,
        *,
        action: str,
        risk: str,
        reason: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        request_id = str(uuid4())
        self.conn.execute(
            """
            INSERT INTO approvals(request_id, action, risk, status, reason, created_at, metadata)
            VALUES (?, ?, ?, 'pending', ?, ?, ?)
            """,
            (
                request_id,
                action,
                risk,
                reason,
                utcnow(),
                json.dumps(metadata or {}, ensure_ascii=False),
            ),
        )
        self.conn.commit()
        return request_id

    def decide_approval(self, request_id: str, status: str) -> None:
        if status not in {"approved", "rejected"}:
            raise ValueError("status must be approved or rejected")
        self.conn.execute(
            "UPDATE approvals SET status = ?, decided_at = ? WHERE request_id = ?",
            (status, utcnow(), request_id),
        )
        self.conn.commit()

    def pending_approvals(self) -> list[ApprovalRecord]:
        rows = self.conn.execute(
            """
            SELECT request_id, action, risk, status, reason, metadata
            FROM approvals
            WHERE status = 'pending'
            ORDER BY created_at ASC
            """
        ).fetchall()
        return [
            ApprovalRecord(
                request_id=str(row["request_id"]),
                action=str(row["action"]),
                risk=str(row["risk"]),
                status=str(row["status"]),
                reason=str(row["reason"]),
                metadata=json.loads(str(row["metadata"])),
            )
            for row in rows
        ]
