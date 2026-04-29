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

from yoloong_ai.config import RuntimeConfig, mask_secret


class ConfigTests(unittest.TestCase):
    def test_from_env_routes_defaults_and_masks_keys(self) -> None:
        env = {
            "DEEPSEEK_API_KEY": "fake-deepseek-secret-value",
            "DASHSCOPE_API_KEY": "fake-dashscope-secret-value",
            "YOLOONG_OFFLINE": "1",
        }
        config = RuntimeConfig.from_env(env=env, root=Path.cwd())

        self.assertEqual(config.assistant_name, "江徽音")
        self.assertEqual(config.region_profile, "china")
        self.assertTrue(config.offline)
        self.assertEqual(config.deepseek.chat_model, "deepseek-v4-pro")
        self.assertEqual(config.dashscope.vision_model, "qwen3-vl-plus")

        diagnostic = config.diagnostic()
        self.assertNotIn("deepseek-secret", str(diagnostic))
        self.assertIn("...", diagnostic["deepseek_api_key"])

    def test_mask_secret_never_returns_full_secret(self) -> None:
        self.assertEqual(mask_secret(None), "<missing>")
        self.assertNotEqual(mask_secret("123456789"), "123456789")


if __name__ == "__main__":
    unittest.main()
