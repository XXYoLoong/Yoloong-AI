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
from http import cookies
import json
from urllib.parse import parse_qs
from typing import Callable

from .auth import SessionSigner, verify_password
from .autonomy import AutonomousAssistant
from .config import RuntimeConfig
from .memory import MemoryStore
from .permissions import Action
from .tools import ChinaAwareResearchTool
from .web import dashboard_page, login_page
from .wechat import OpenClawWeChatNormalizer, OutgoingMessage


class AssistantHTTPHandler(BaseHTTPRequestHandler):
    assistant_factory: Callable[[], AutonomousAssistant]
    config: RuntimeConfig
    normalizer = OpenClawWeChatNormalizer()

    def do_GET(self) -> None:
        path = self._strip_base_path()
        if path == "/health":
            self._send_json({"ok": True})
            return
        if path in {"", "/"}:
            if not self._session():
                self._send_html(login_page(self.config))
                return
            self._send_html(dashboard_page(self.config))
            return
        if path == "/logout":
            self._redirect("/", clear_session=True)
            return
        if path == "/api/status":
            if not self._require_auth():
                return
            self._send_json({"ok": True, "config": self.config.diagnostic()})
            return
        if path == "/api/approvals":
            if not self._require_auth():
                return
            store = MemoryStore(self.config.db_path)
            try:
                approvals = [record.__dict__ for record in store.pending_approvals()]
            finally:
                store.close()
            self._send_json({"approvals": approvals})
            return
        self.send_error(404)

    def do_POST(self) -> None:
        path = self._strip_base_path()
        if path == "/login":
            self._handle_login()
            return
        if path == "/wechat/message":
            self._handle_wechat_message()
            return
        if not self._require_auth():
            return
        if path == "/api/chat":
            payload = self._read_json()
            assistant = self.__class__.assistant_factory()
            try:
                output = assistant.handle_user_message(str(payload.get("text", "")), channel="web", sender="admin")
            finally:
                assistant.close()
            self._send_json({"text": output.text})
            return
        if path == "/api/tick":
            assistant = self.__class__.assistant_factory()
            try:
                output = assistant.tick()
            finally:
                assistant.close()
            self._send_json(
                {
                    "text": output.text,
                    "action": output.action.__dict__ if output.action else None,
                    "risk": {
                        "level": output.risk.level.value,
                        "requires_confirmation": output.risk.requires_confirmation,
                        "reason": output.risk.reason,
                    }
                    if output.risk
                    else None,
                    "approval_request_id": output.approval_request_id,
                }
            )
            return
        if path == "/api/propose":
            payload = self._read_json()
            assistant = self.__class__.assistant_factory()
            try:
                output = assistant.propose_core_action(
                    Action(
                        name=str(payload.get("name", "manual_action")),
                        description=str(payload.get("description", "手动动作")),
                        target=str(payload.get("target", "")),
                        metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
                    )
                )
            finally:
                assistant.close()
            self._send_json({"text": output.text, "approval_request_id": output.approval_request_id})
            return
        if path == "/api/memory":
            payload = self._read_json()
            store = MemoryStore(self.config.db_path)
            try:
                store.set_memory(str(payload.get("key", "")).strip(), str(payload.get("value", "")).strip(), 3)
            finally:
                store.close()
            self._send_json({"ok": True})
            return
        if path == "/api/memory/search":
            payload = self._read_json()
            store = MemoryStore(self.config.db_path)
            try:
                results = store.search_memories(str(payload.get("query", "")))
            finally:
                store.close()
            self._send_json({"results": results})
            return
        if path == "/api/research/queries":
            payload = self._read_json()
            tool = ChinaAwareResearchTool()
            queries = tool.build_queries(str(payload.get("topic", "")))
            self._send_json({"queries": queries, "preferred_domains": tool.preferred_domains()})
            return
        self.send_error(404)

    def _handle_wechat_message(self) -> None:
        if self._strip_base_path() != "/wechat/message":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        payload = json.loads(raw or "{}")
        message = self.normalizer.normalize(payload)
        assistant = self.__class__.assistant_factory()
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

    def _handle_login(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        fields = parse_qs(body)
        username = fields.get("username", [""])[0]
        password = fields.get("password", [""])[0]
        if username != self.config.admin_user or not verify_password(password, self.config.admin_password_hash):
            self._send_html(login_page(self.config, "账号或密码不对。"), status=401)
            return
        if not self.config.session_secret:
            self._send_html(login_page(self.config, "服务端缺少会话密钥。"), status=500)
            return
        token = SessionSigner(self.config.session_secret).issue(username)
        self._redirect("/", session_token=token)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _strip_base_path(self) -> str:
        path = self.path.split("?", 1)[0]
        base = self.config.web_base_path
        if base != "/" and path.startswith(base):
            path = path[len(base) :]
            if not path:
                path = "/"
        return path

    def _read_json(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        if not raw:
            return {}
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}

    def _session(self):
        if not self.config.session_secret:
            return None
        raw_cookie = self.headers.get("Cookie", "")
        parsed = cookies.SimpleCookie(raw_cookie)
        morsel = parsed.get("yoloong_session")
        token = morsel.value if morsel else None
        return SessionSigner(self.config.session_secret).verify(token)

    def _require_auth(self) -> bool:
        if self._session():
            return True
        self._send_json({"error": "unauthorized"}, status=401)
        return False

    def _redirect(self, path: str, *, session_token: str | None = None, clear_session: bool = False) -> None:
        target = self.config.web_base_path if path == "/" else self.config.web_base_path + path
        self.send_response(303)
        self.send_header("Location", target)
        if session_token:
            self.send_header(
                "Set-Cookie",
                f"yoloong_session={session_token}; HttpOnly; SameSite=Lax; Secure; Path={self.config.web_base_path}",
            )
        if clear_session:
            self.send_header(
                "Set-Cookie",
                f"yoloong_session=; Max-Age=0; HttpOnly; SameSite=Lax; Secure; Path={self.config.web_base_path}",
            )
        self.end_headers()

    def _send_html(self, html_text: str, status: int = 200) -> None:
        body = html_text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

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
    config: RuntimeConfig,
) -> None:
    AssistantHTTPHandler.assistant_factory = assistant_factory
    AssistantHTTPHandler.config = config
    server = ThreadingHTTPServer((host, port), AssistantHTTPHandler)
    server.serve_forever()
