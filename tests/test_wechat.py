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

import unittest

from yoloong_ai.wechat import OpenClawWeChatNormalizer, OutgoingMessage


class WeChatTests(unittest.TestCase):
    def test_normalizes_openclaw_like_payload(self) -> None:
        payload = {
            "data": {
                "from": "wxid-user",
                "conversation_id": "chat-1",
                "message": {"text": "我回来了"},
            }
        }
        message = OpenClawWeChatNormalizer().normalize(payload)

        self.assertEqual(message.sender, "wxid-user")
        self.assertEqual(message.text, "我回来了")
        self.assertEqual(message.conversation_id, "chat-1")

    def test_outgoing_payload(self) -> None:
        payload = OutgoingMessage("chat-1", "我在呢").to_openclaw_payload()

        self.assertEqual(payload["type"], "text")
        self.assertEqual(payload["to"], "chat-1")
        self.assertEqual(payload["text"], "我在呢")


if __name__ == "__main__":
    unittest.main()
