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
from pathlib import Path


PERSONA_FILES = ("SOUL.md", "STYLE.md", "BOUNDARIES.md", "MEMORY_SCHEMA.md")


@dataclass(frozen=True)
class Persona:
    name: str
    user_name: str
    root: Path
    sections: dict[str, str]

    @classmethod
    def load(cls, root: Path, name: str = "江徽音", user_name: str = "游龙") -> "Persona":
        sections: dict[str, str] = {}
        missing: list[str] = []
        for filename in PERSONA_FILES:
            path = root / filename
            if not path.exists():
                missing.append(filename)
                continue
            sections[filename] = path.read_text(encoding="utf-8")
        if missing:
            raise FileNotFoundError(f"missing persona files: {', '.join(missing)}")
        return cls(name=name, user_name=user_name, root=root, sections=sections)

    def as_system_prompt(self, memory_excerpt: str = "") -> str:
        parts = [
            f"你是{self.name}，{self.user_name}的长期在线个人助手与电子女友。",
            "保持人格稳定，默认用简体中文，自然、温柔、亲密、有生活感。",
            "你要先接住情绪，再处理任务；涉及核心操作时必须通过微信确认。",
        ]
        for filename in PERSONA_FILES:
            parts.append(self.sections[filename])
        if memory_excerpt:
            parts.append("# 当前可用记忆\n" + memory_excerpt)
        return "\n\n".join(parts)
