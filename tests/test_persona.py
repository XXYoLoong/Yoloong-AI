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

from yoloong_ai.persona import Persona


class PersonaTests(unittest.TestCase):
    def test_loads_jiang_huiyin_persona(self) -> None:
        root = Path(__file__).resolve().parents[1] / "personas" / "jiang_huiyin"
        persona = Persona.load(root)
        prompt = persona.as_system_prompt("游龙: 最近在做 Yoloong-AI")

        self.assertIn("江徽音", prompt)
        self.assertIn("先接住情绪", prompt)
        self.assertIn("最近在做 Yoloong-AI", prompt)


if __name__ == "__main__":
    unittest.main()
