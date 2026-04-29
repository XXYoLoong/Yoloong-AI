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
from typing import Any


@dataclass(frozen=True)
class WeChatMessage:
    sender: str
    text: str
    conversation_id: str = ""
    raw: dict[str, Any] | None = None


@dataclass(frozen=True)
class OutgoingMessage:
    recipient: str
    text: str

    def to_openclaw_payload(self) -> dict[str, str]:
        return {"type": "text", "to": self.recipient, "text": self.text}


class OpenClawWeChatNormalizer:
    def normalize(self, payload: dict[str, Any]) -> WeChatMessage:
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        text = self._first_text(
            data.get("text"),
            data.get("content"),
            data.get("message"),
            payload.get("text"),
            payload.get("content"),
        )
        if not text and isinstance(data.get("item_list"), list) and data["item_list"]:
            first = data["item_list"][0]
            if isinstance(first, dict):
                text = self._first_text(first.get("text"), first.get("content"))
        sender = str(
            data.get("sender")
            or data.get("from")
            or data.get("from_user")
            or data.get("wxid")
            or payload.get("sender")
            or "unknown"
        )
        conversation_id = str(
            data.get("conversation_id")
            or data.get("roomid")
            or data.get("chat_id")
            or payload.get("conversation_id")
            or sender
        )
        return WeChatMessage(
            sender=sender,
            text=text.strip(),
            conversation_id=conversation_id,
            raw=payload,
        )

    def _first_text(self, *values: Any) -> str:
        for value in values:
            if isinstance(value, str) and value.strip():
                return value
            if isinstance(value, dict):
                nested = self._first_text(value.get("text"), value.get("content"))
                if nested:
                    return nested
        return ""
