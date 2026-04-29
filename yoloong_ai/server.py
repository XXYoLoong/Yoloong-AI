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

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from typing import Callable

from .autonomy import AutonomousAssistant
from .wechat import OpenClawWeChatNormalizer, OutgoingMessage


class AssistantHTTPHandler(BaseHTTPRequestHandler):
    assistant_factory: Callable[[], AutonomousAssistant]
    normalizer = OpenClawWeChatNormalizer()

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json({"ok": True})
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/wechat/message":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        payload = json.loads(raw or "{}")
        message = self.normalizer.normalize(payload)
        assistant = self.assistant_factory()
        try:
            output = assistant.handle_user_message(
                message.text,
                channel="wechat",
                sender=message.sender,
            )
        finally:
            assistant.close()
        response = OutgoingMessage(message.conversation_id, output.text).to_openclaw_payload()
        self._send_json(response)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(
    host: str,
    port: int,
    assistant_factory: Callable[[], AutonomousAssistant],
) -> None:
    AssistantHTTPHandler.assistant_factory = assistant_factory
    server = ThreadingHTTPServer((host, port), AssistantHTTPHandler)
    server.serve_forever()
