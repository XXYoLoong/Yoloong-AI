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

from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib import error, parse, request
import json
import tempfile
import unittest

from yoloong_ai.auth import hash_password
from yoloong_ai.cli import build_assistant
from yoloong_ai.config import RuntimeConfig
from yoloong_ai.server import AssistantHTTPHandler
from yoloong_ai.web import dashboard_page, login_page


class WebTests(unittest.TestCase):
    def config(self, tmp: str) -> RuntimeConfig:
        return RuntimeConfig.from_env(
            env={
                "YOLOONG_OFFLINE": "1",
                "YOLOONG_DB_PATH": str(Path(tmp) / "web.sqlite3"),
                "YOLOONG_WEB_BASE_PATH": "/ai",
                "YOLOONG_ADMIN_USER": "yoloong",
                "YOLOONG_ADMIN_PASSWORD_HASH": hash_password("passw0rd!"),
                "YOLOONG_SESSION_SECRET": "test-session-secret",
                "DEEPSEEK_API_KEY": "deepseek",
                "DASHSCOPE_API_KEY": "dashscope",
            },
            root=Path(__file__).resolve().parents[1],
        )

    def test_pages_render_console_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.config(tmp)

            self.assertIn("江徽音控制台", login_page(config))
            self.assertIn("线上调试与自主决策面板", dashboard_page(config))
            self.assertIn("/ai/login", login_page(config))

    def test_http_auth_and_chat_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.config(tmp)
            AssistantHTTPHandler.config = config
            AssistantHTTPHandler.assistant_factory = lambda: build_assistant(config)
            server = ThreadingHTTPServer(("127.0.0.1", 0), AssistantHTTPHandler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}/ai"
            try:
                with self.assertRaises(error.HTTPError) as ctx:
                    request.urlopen(base + "/api/status", timeout=5)
                self.assertEqual(ctx.exception.code, 401)

                form = parse.urlencode({"username": "yoloong", "password": "passw0rd!"}).encode()
                login_req = request.Request(base + "/login", data=form, method="POST")
                opener = request.build_opener(NoRedirectHandler)
                try:
                    response = opener.open(login_req, timeout=5)
                except error.HTTPError as exc:
                    self.assertEqual(exc.code, 303)
                    response = exc
                cookie = response.headers["Set-Cookie"]
                self.assertIn("yoloong_session=", cookie)

                payload = json.dumps({"text": "我回来了"}).encode("utf-8")
                chat_req = request.Request(
                    base + "/api/chat",
                    data=payload,
                    headers={"Content-Type": "application/json", "Cookie": cookie},
                    method="POST",
                )
                chat = json.loads(request.urlopen(chat_req, timeout=5).read().decode("utf-8"))
                self.assertIn("回来", chat["text"])
            finally:
                server.shutdown()
                server.server_close()


class NoRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


if __name__ == "__main__":
    unittest.main()
