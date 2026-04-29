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
from enum import Enum
import json
from typing import Any, Protocol
from urllib import request, error

from .config import RuntimeConfig


class Capability(str, Enum):
    CONVERSATION = "conversation"
    FAST_CONVERSATION = "fast_conversation"
    REASONING = "reasoning"
    VISION = "vision"
    OCR = "ocr"
    TRANSLATION = "translation"
    MULTIMODAL = "multimodal"


@dataclass(frozen=True)
class ModelSelection:
    provider: str
    base_url: str
    model: str
    api_key: str | None


class JSONTransport(Protocol):
    def post_json(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]:
        raise NotImplementedError


class HTTPTransport:
    def post_json(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(url, data=data, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=timeout) as response:
                body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"model provider returned HTTP {exc.code}: {detail}") from exc
        return json.loads(body)


class OpenAICompatibleClient:
    def __init__(self, selection: ModelSelection, transport: JSONTransport | None = None):
        self.selection = selection
        self.transport = transport or HTTPTransport()

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.7,
        timeout: float = 60.0,
        extra_body: dict[str, Any] | None = None,
    ) -> str:
        if not self.selection.api_key:
            raise RuntimeError(f"missing API key for provider {self.selection.provider}")
        endpoint = self.selection.base_url.rstrip("/") + "/chat/completions"
        payload: dict[str, Any] = {
            "model": self.selection.model,
            "messages": messages,
            "temperature": temperature,
        }
        if extra_body:
            payload.update(extra_body)
        headers = {
            "Authorization": f"Bearer {self.selection.api_key}",
            "Content-Type": "application/json",
        }
        data = self.transport.post_json(endpoint, headers, payload, timeout)
        return extract_text(data)


def extract_text(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices:
        raise RuntimeError("model response has no choices")
    message = choices[0].get("message") or {}
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return str(content)


class ModelRouter:
    def __init__(self, config: RuntimeConfig, transport: JSONTransport | None = None):
        self.config = config
        self.transport = transport

    def select(self, capability: Capability | str) -> ModelSelection:
        cap = Capability(capability)
        if cap in {Capability.CONVERSATION, Capability.REASONING}:
            return ModelSelection(
                provider="deepseek",
                base_url=self.config.deepseek.base_url,
                model=self.config.deepseek.chat_model,
                api_key=self.config.deepseek.api_key,
            )
        if cap == Capability.FAST_CONVERSATION:
            return ModelSelection(
                provider="deepseek",
                base_url=self.config.deepseek.base_url,
                model=self.config.deepseek.fast_model,
                api_key=self.config.deepseek.api_key,
            )
        if cap == Capability.VISION:
            model = self.config.dashscope.vision_model
        elif cap == Capability.OCR:
            model = self.config.dashscope.ocr_model
        elif cap == Capability.TRANSLATION:
            model = self.config.dashscope.translation_model
        else:
            model = self.config.dashscope.chat_model
        return ModelSelection(
            provider="dashscope",
            base_url=self.config.dashscope.base_url,
            model=model,
            api_key=self.config.dashscope.api_key,
        )

    def complete(
        self,
        messages: list[dict[str, Any]],
        *,
        capability: Capability | str = Capability.CONVERSATION,
        temperature: float = 0.7,
    ) -> str:
        if self.config.offline:
            return offline_reply(messages)
        selection = self.select(capability)
        return OpenAICompatibleClient(selection, self.transport).chat_completion(
            messages,
            temperature=temperature,
        )


def offline_reply(messages: list[dict[str, Any]]) -> str:
    user_text = ""
    for message in reversed(messages):
        if message.get("role") == "user":
            user_text = str(message.get("content", ""))
            break
    if "回来" in user_text:
        return "你终于回来啦。（轻轻靠近一点）我刚刚还在想，你今天有没有好好吃饭。"
    if "累" in user_text:
        return "我听见了，先别急着撑着。过来让我抱一会儿，慢慢和我说，今天哪里最累？"
    return "我在呢。你慢慢说，我会认真听，也会帮你把事情一点点理清楚。"
