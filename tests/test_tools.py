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

from yoloong_ai.tools import ChinaAwareResearchTool, parse_duckduckgo_html


class ToolTests(unittest.TestCase):
    def test_parse_duckduckgo_html_result(self) -> None:
        html = """
        <html><body>
        <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.gov.cn%2Ftest">国务院</a>
        </body></html>
        """
        results = parse_duckduckgo_html(html)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "国务院")
        self.assertEqual(results[0].url, "https://www.gov.cn/test")

    def test_china_research_queries_prioritize_official_sources(self) -> None:
        tool = ChinaAwareResearchTool()
        queries = tool.build_queries("全国天气")

        self.assertTrue(any("site:gov.cn" in query for query in queries))
        self.assertIn("gov.cn", tool.preferred_domains())


if __name__ == "__main__":
    unittest.main()
