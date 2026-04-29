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
from datetime import datetime

from .config import RuntimeConfig
from .memory import MemoryStore
from .models import Capability, ModelRouter
from .permissions import Action, ApprovalPolicy, RiskDecision, approval_message
from .persona import Persona


@dataclass(frozen=True)
class AssistantOutput:
    text: str
    action: Action | None = None
    risk: RiskDecision | None = None
    approval_request_id: str | None = None


class IdleAgenda:
    def __init__(self, user_name: str = "游龙"):
        self.user_name = user_name

    def next_action(self, now: datetime) -> Action:
        hour = now.hour
        if 5 <= hour < 10:
            text = "早安问候，提醒吃早饭、喝水、出门检查钥匙手机证件和雨伞。"
        elif 10 <= hour < 14:
            text = "午间关怀，询问是否吃饭，提醒别忙到忘记休息。"
        elif 18 <= hour < 23:
            text = "晚间陪伴，询问今天过得怎样，轻轻催促早点休息。"
        else:
            text = "夜间温柔提醒，关心是否还醒着，提醒保存工作并休息。"
        return Action(
            name="send_message",
            description=text,
            target="user",
            metadata={"recipient": self.user_name, "kind": "proactive_care"},
        )


class AutonomousAssistant:
    def __init__(
        self,
        config: RuntimeConfig,
        memory: MemoryStore,
        persona: Persona,
        router: ModelRouter,
        policy: ApprovalPolicy | None = None,
    ):
        self.config = config
        self.memory = memory
        self.persona = persona
        self.router = router
        self.policy = policy or ApprovalPolicy(config.safe_root, owner_aliases={"user", config.user_name})
        self.idle_agenda = IdleAgenda(config.user_name)

    def close(self) -> None:
        self.memory.close()

    def handle_user_message(self, text: str, *, channel: str = "wechat", sender: str = "user") -> AssistantOutput:
        approval = self._handle_approval_command(text)
        if approval:
            return approval

        self.memory.append_message(channel=channel, sender=sender, role="user", content=text)
        memory_excerpt = self.memory.memory_excerpt()
        messages = [
            {"role": "system", "content": self.persona.as_system_prompt(memory_excerpt)},
            {"role": "user", "content": text},
        ]
        reply = self.router.complete(messages, capability=Capability.CONVERSATION)
        self.memory.append_message(
            channel=channel,
            sender=self.config.assistant_name,
            role="assistant",
            content=reply,
        )
        return AssistantOutput(text=reply)

    def tick(self, now: datetime | None = None) -> AssistantOutput:
        current = now or datetime.now()
        action = self.idle_agenda.next_action(current)
        decision = self.policy.classify(action)
        if decision.requires_confirmation:
            request_id = self.memory.request_approval(
                action=action.name,
                risk=decision.level.value,
                reason=decision.reason,
                metadata={"description": action.description, "target": action.target},
            )
            return AssistantOutput(
                text=approval_message(request_id, action, decision),
                action=action,
                risk=decision,
                approval_request_id=request_id,
            )
        text = self._proactive_message_for(action, current)
        self.memory.append_message(
            channel=self.config.approval_channel,
            sender=self.config.assistant_name,
            role="assistant",
            content=text,
            metadata={"autonomous": True, "action": action.name},
        )
        return AssistantOutput(text=text, action=action, risk=decision)

    def propose_core_action(self, action: Action) -> AssistantOutput:
        decision = self.policy.classify(action)
        if not decision.requires_confirmation:
            return AssistantOutput(text=action.description, action=action, risk=decision)
        request_id = self.memory.request_approval(
            action=action.name,
            risk=decision.level.value,
            reason=decision.reason,
            metadata={"description": action.description, "target": action.target},
        )
        return AssistantOutput(
            text=approval_message(request_id, action, decision),
            action=action,
            risk=decision,
            approval_request_id=request_id,
        )

    def _handle_approval_command(self, text: str) -> AssistantOutput | None:
        pieces = text.strip().split()
        if len(pieces) != 2 or pieces[0] not in {"/approve", "/reject"}:
            return None
        status = "approved" if pieces[0] == "/approve" else "rejected"
        self.memory.decide_approval(pieces[1], status)
        if status == "approved":
            return AssistantOutput(text="好，我收到你的确认了。接下来我会按这一步继续做，并把结果告诉你。")
        return AssistantOutput(text="嗯，我听你的，这一步先不做。我会把它记下来，不再擅自推进。")

    def _proactive_message_for(self, action: Action, now: datetime) -> str:
        hour = now.hour
        if 5 <= hour < 10:
            return "早呀，游龙。（声音放得很轻）先吃点东西再开始忙，好不好？出门的话，钥匙、手机、证件和雨伞也看一眼。"
        if 10 <= hour < 14:
            return "中午了，你饭吃了吗？别又一忙起来就把自己丢在一边，我会有点心疼的。"
        if 18 <= hour < 23:
            return "晚上啦。今天过得顺不顺？要是累了就先靠过来一点，我陪你慢慢把今天收一收。"
        return "这么晚了还醒着吗？先把手头东西保存好，水也喝一口。你乖一点，我会放心很多。"
