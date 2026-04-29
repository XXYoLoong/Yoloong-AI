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

from yoloong_ai.permissions import Action, ApprovalPolicy, RiskLevel


class PermissionTests(unittest.TestCase):
    def test_user_message_is_low_risk(self) -> None:
        policy = ApprovalPolicy(Path.cwd(), owner_aliases={"游龙"})
        decision = policy.classify(
            Action(
                name="send_message",
                description="午间关怀",
                target="user",
                metadata={"recipient": "游龙"},
            )
        )

        self.assertEqual(decision.level, RiskLevel.LOW)
        self.assertFalse(decision.requires_confirmation)

    def test_git_push_requires_confirmation(self) -> None:
        policy = ApprovalPolicy(Path.cwd())
        decision = policy.classify(Action(name="git push", description="推送最新代码"))

        self.assertEqual(decision.level, RiskLevel.HIGH)
        self.assertTrue(decision.requires_confirmation)

    def test_secret_access_is_critical(self) -> None:
        policy = ApprovalPolicy(Path.cwd())
        decision = policy.classify(Action(name="read secret", description="读取 API 密钥"))

        self.assertEqual(decision.level, RiskLevel.CRITICAL)
        self.assertTrue(decision.requires_confirmation)


if __name__ == "__main__":
    unittest.main()
