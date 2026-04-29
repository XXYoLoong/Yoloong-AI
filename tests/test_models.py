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

from pathlib import Path
from typing import Any
import unittest

from yoloong_ai.config import RuntimeConfig
from yoloong_ai.models import Capability, ModelRouter


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str], dict[str, Any]]] = []

    def post_json(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]:
        self.calls.append((url, headers, payload))
        return {"choices": [{"message": {"content": "ok"}}]}


class ModelRouterTests(unittest.TestCase):
    def config(self) -> RuntimeConfig:
        return RuntimeConfig.from_env(
            env={
                "DEEPSEEK_API_KEY": "deepseek-key",
                "DASHSCOPE_API_KEY": "dashscope-key",
            },
            root=Path.cwd(),
        )

    def test_conversation_uses_deepseek(self) -> None:
        router = ModelRouter(self.config())
        selected = router.select(Capability.CONVERSATION)

        self.assertEqual(selected.provider, "deepseek")
        self.assertEqual(selected.model, "deepseek-v4-pro")

    def test_vision_uses_dashscope_qwen(self) -> None:
        router = ModelRouter(self.config())
        selected = router.select(Capability.VISION)

        self.assertEqual(selected.provider, "dashscope")
        self.assertEqual(selected.model, "qwen3-vl-plus")

    def test_completion_uses_openai_compatible_endpoint(self) -> None:
        transport = FakeTransport()
        router = ModelRouter(self.config(), transport=transport)
        text = router.complete([{"role": "user", "content": "hi"}])

        self.assertEqual(text, "ok")
        url, headers, payload = transport.calls[0]
        self.assertTrue(url.endswith("/chat/completions"))
        self.assertEqual(headers["Authorization"], "Bearer deepseek-key")
        self.assertEqual(payload["model"], "deepseek-v4-pro")


if __name__ == "__main__":
    unittest.main()
