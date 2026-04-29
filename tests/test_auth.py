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

from yoloong_ai.auth import SessionSigner, generate_password, hash_password, verify_password


class AuthTests(unittest.TestCase):
    def test_password_hash_round_trip(self) -> None:
        encoded = hash_password("private-password")

        self.assertTrue(verify_password("private-password", encoded))
        self.assertFalse(verify_password("wrong-password", encoded))
        self.assertNotIn("private-password", encoded)

    def test_session_signer_rejects_tampering(self) -> None:
        signer = SessionSigner("session-secret")
        token = signer.issue("yoloong")

        self.assertEqual(signer.verify(token).username, "yoloong")
        self.assertIsNone(signer.verify(token + "x"))

    def test_generate_password_has_length(self) -> None:
        self.assertGreaterEqual(len(generate_password()), 20)


if __name__ == "__main__":
    unittest.main()
