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

from datetime import datetime
from pathlib import Path
import tempfile
import unittest

from yoloong_ai.autonomy import AutonomousAssistant
from yoloong_ai.config import RuntimeConfig
from yoloong_ai.memory import MemoryStore
from yoloong_ai.models import ModelRouter
from yoloong_ai.permissions import Action
from yoloong_ai.persona import Persona


class AutonomyTests(unittest.TestCase):
    def assistant(self, tmp: str) -> AutonomousAssistant:
        root = Path(__file__).resolve().parents[1]
        config = RuntimeConfig.from_env(
            env={
                "YOLOONG_OFFLINE": "1",
                "YOLOONG_DB_PATH": str(Path(tmp) / "memory.sqlite3"),
                "DEEPSEEK_API_KEY": "deepseek",
                "DASHSCOPE_API_KEY": "dashscope",
            },
            root=root,
        )
        return AutonomousAssistant(
            config,
            MemoryStore(config.db_path),
            Persona.load(config.persona_dir),
            ModelRouter(config),
        )

    def test_idle_tick_generates_proactive_care_without_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            assistant = self.assistant(tmp)
            try:
                output = assistant.tick(datetime.fromisoformat("2026-04-29T08:30:00"))
            finally:
                assistant.close()

            self.assertIn("早", output.text)
            self.assertIsNotNone(output.action)
            self.assertFalse(output.risk.requires_confirmation)

    def test_core_action_creates_approval_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            assistant = self.assistant(tmp)
            try:
                output = assistant.propose_core_action(
                    Action(name="git push", description="推送最新代码到 GitHub")
                )
            finally:
                assistant.close()

            self.assertIn("/approve", output.text)
            self.assertIsNotNone(output.approval_request_id)
            self.assertTrue(output.risk.requires_confirmation)

    def test_offline_chat_keeps_persona_tone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            assistant = self.assistant(tmp)
            try:
                output = assistant.handle_user_message("我回来了")
            finally:
                assistant.close()

            self.assertIn("回来", output.text)
            self.assertIn("吃饭", output.text)


if __name__ == "__main__":
    unittest.main()
