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

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Action:
    name: str
    description: str
    target: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RiskDecision:
    level: RiskLevel
    requires_confirmation: bool
    reason: str


class ApprovalPolicy:
    def __init__(self, safe_root: Path, owner_aliases: set[str] | None = None):
        self.safe_root = safe_root.resolve()
        self.owner_aliases = owner_aliases or {"user", "游龙", "owner", "self"}

    def classify(self, action: Action) -> RiskDecision:
        name = action.name.lower()
        target = action.target.lower()
        text = f"{name} {target} {action.description.lower()}"

        if any(word in text for word in ("secret", "password", "private key", "cookie", "密钥", "密码")):
            return RiskDecision(RiskLevel.CRITICAL, True, "涉及密钥或敏感凭据")
        if any(word in text for word in ("payment", "transfer", "purchase", "subscribe", "支付", "转账", "购买")):
            return RiskDecision(RiskLevel.CRITICAL, True, "涉及支付或资金操作")
        if any(word in text for word in ("delete", "overwrite", "move", "rm ", "删除", "覆盖", "移动")):
            return RiskDecision(RiskLevel.HIGH, True, "可能破坏或丢失文件")
        if any(word in text for word in ("server", "systemctl", "install", "restart", "ssh", "服务器", "重启")):
            return RiskDecision(RiskLevel.HIGH, True, "涉及服务器或系统配置")
        if any(word in text for word in ("git push", "commit", "release", "publish", "发布", "推送")):
            return RiskDecision(RiskLevel.HIGH, True, "涉及代码发布或远程变更")
        if name in {"send_message", "wechat_send"}:
            recipient = str(action.metadata.get("recipient", action.target or "user"))
            if recipient in self.owner_aliases:
                return RiskDecision(RiskLevel.LOW, False, "只向用户本人发送低风险消息")
            return RiskDecision(RiskLevel.HIGH, True, "向用户以外对象发送消息")
        if name in {"web_search", "research", "daily_brief", "project_review"}:
            return RiskDecision(RiskLevel.LOW, False, "只读或生成类动作")
        if "file_path" in action.metadata:
            path = Path(str(action.metadata["file_path"])).resolve()
            if not self._inside_safe_root(path):
                return RiskDecision(RiskLevel.HIGH, True, "目标路径超出安全根目录")
        return RiskDecision(RiskLevel.MEDIUM, False, "普通助手动作")

    def _inside_safe_root(self, path: Path) -> bool:
        try:
            path.relative_to(self.safe_root)
        except ValueError:
            return False
        return True


def approval_message(request_id: str, action: Action, decision: RiskDecision) -> str:
    return (
        "游龙，这件事我需要你确认一下再做。\n"
        f"动作：{action.description}\n"
        f"风险：{decision.level.value}，原因：{decision.reason}\n"
        f"确认执行请回复：/approve {request_id}\n"
        f"不执行请回复：/reject {request_id}"
    )
