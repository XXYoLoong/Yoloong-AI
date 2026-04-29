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

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Iterable
from urllib import parse, request


CHINA_PRIORITY_DOMAINS = (
    "gov.cn",
    "stats.gov.cn",
    "weather.com.cn",
    "people.com.cn",
    "xinhuanet.com",
    "mfa.gov.cn",
    "nea.gov.cn",
    "miit.gov.cn",
)


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""


class DuckDuckGoParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[SearchResult] = []
        self._in_title = False
        self._title: list[str] = []
        self._href = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        classes = values.get("class", "")
        if tag == "a" and "result__a" in classes:
            self._in_title = True
            self._title = []
            self._href = values.get("href", "") or ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_title:
            title = " ".join("".join(self._title).split())
            if title and self._href:
                self.results.append(SearchResult(title=title, url=decode_duckduckgo_url(self._href)))
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title.append(data)


def decode_duckduckgo_url(url: str) -> str:
    if url.startswith("//"):
        url = "https:" + url
    parsed = parse.urlparse(url)
    params = parse.parse_qs(parsed.query)
    if "uddg" in params:
        return params["uddg"][0]
    return url


class WebSearchTool:
    def __init__(self, timeout: float = 12.0):
        self.timeout = timeout

    def build_url(self, query: str, region: str = "china") -> str:
        params = {"q": query}
        if region == "china":
            params["kl"] = "cn-zh"
        return "https://html.duckduckgo.com/html/?" + parse.urlencode(params)

    def search(self, query: str, *, region: str = "china", max_results: int = 5) -> list[SearchResult]:
        url = self.build_url(query, region=region)
        req = request.Request(url, headers={"User-Agent": "Yoloong-AI/0.1"})
        with request.urlopen(req, timeout=self.timeout) as response:
            html = response.read().decode("utf-8", errors="replace")
        return parse_duckduckgo_html(html)[:max_results]


def parse_duckduckgo_html(html: str) -> list[SearchResult]:
    parser = DuckDuckGoParser()
    parser.feed(html)
    return parser.results


class ChinaAwareResearchTool:
    def __init__(self, search_tool: WebSearchTool | None = None):
        self.search_tool = search_tool or WebSearchTool()

    def build_queries(self, topic: str) -> list[str]:
        return [
            f"{topic} site:gov.cn",
            f"{topic} site:stats.gov.cn OR site:people.com.cn",
            f"{topic} site:xinhuanet.com OR site:weather.com.cn",
            topic,
        ]

    def preferred_domains(self) -> tuple[str, ...]:
        return CHINA_PRIORITY_DOMAINS

    def collect(self, topic: str, *, max_results: int = 8) -> list[SearchResult]:
        seen: set[str] = set()
        collected: list[SearchResult] = []
        for query in self.build_queries(topic):
            for result in self.search_tool.search(query, region="china", max_results=max_results):
                if result.url in seen:
                    continue
                seen.add(result.url)
                collected.append(result)
                if len(collected) >= max_results:
                    return self._rank(collected)
        return self._rank(collected)

    def _rank(self, results: Iterable[SearchResult]) -> list[SearchResult]:
        def score(result: SearchResult) -> int:
            return sum(1 for domain in CHINA_PRIORITY_DOMAINS if domain in result.url)

        return sorted(results, key=score, reverse=True)
