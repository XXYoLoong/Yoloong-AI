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
import tempfile
import unittest

from yoloong_ai.memory import MemoryStore


class MemoryTests(unittest.TestCase):
    def test_memory_message_and_approval_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MemoryStore(Path(tmp) / "memory.sqlite3")
            store.set_memory("breakfast", "游龙早上不要空腹", importance=5)
            store.append_message(channel="wechat", sender="user", role="user", content="我回来了")
            request_id = store.request_approval(
                action="git push",
                risk="high",
                reason="远程变更",
            )

            self.assertEqual(store.get_memory("breakfast"), "游龙早上不要空腹")
            self.assertIn("breakfast", store.memory_excerpt())
            self.assertEqual(len(store.pending_approvals()), 1)

            store.decide_approval(request_id, "approved")
            self.assertEqual(len(store.pending_approvals()), 0)
            store.close()


if __name__ == "__main__":
    unittest.main()
