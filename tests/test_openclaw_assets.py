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
import unittest


class OpenClawAssetTests(unittest.TestCase):
    def test_workspace_assets_exist(self) -> None:
        root = Path(__file__).resolve().parents[1] / "openclaw" / "workspace"

        for name in ("SOUL.md", "AGENTS.md", "TOOLS.md"):
            self.assertTrue((root / name).exists(), name)

        self.assertIn("江徽音", (root / "SOUL.md").read_text(encoding="utf-8"))
        self.assertIn("DeepSeek", (root / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertIn("微信确认", (root / "TOOLS.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
