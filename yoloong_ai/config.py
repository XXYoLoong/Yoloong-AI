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
import os
from pathlib import Path
from typing import Mapping


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(value: str | None, default: int) -> int:
    if value is None or not value.strip():
        return default
    return int(value)


def mask_secret(value: str | None) -> str:
    """Return a non-reversible display string for a secret."""
    if not value:
        return "<missing>"
    if len(value) <= 8:
        return f"<present:{len(value)}>"
    return f"{value[:3]}...{value[-3:]}:{len(value)}"


@dataclass(frozen=True)
class DeepSeekConfig:
    api_key: str | None
    base_url: str = "https://api.deepseek.com"
    chat_model: str = "deepseek-v4-pro"
    fast_model: str = "deepseek-v4-flash"


@dataclass(frozen=True)
class DashScopeConfig:
    api_key: str | None
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    chat_model: str = "qwen3.6-plus"
    vision_model: str = "qwen3-vl-plus"
    ocr_model: str = "qwen-vl-ocr-latest"
    translation_model: str = "qwen-mt-plus"


@dataclass(frozen=True)
class RuntimeConfig:
    assistant_name: str
    user_name: str
    persona_dir: Path
    data_dir: Path
    db_path: Path
    safe_root: Path
    region_profile: str
    approval_channel: str
    idle_interval_seconds: int
    offline: bool
    web_base_path: str
    public_url: str
    admin_user: str
    admin_password_hash: str | None
    session_secret: str | None
    deepseek: DeepSeekConfig
    dashscope: DashScopeConfig

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        root: Path | None = None,
    ) -> "RuntimeConfig":
        source = env if env is not None else os.environ
        project_root = root or Path.cwd()
        data_dir = Path(source.get("YOLOONG_DATA_DIR", ".runtime"))
        db_path = Path(source.get("YOLOONG_DB_PATH", str(data_dir / "yoloong.sqlite3")))
        persona_dir = Path(source.get("YOLOONG_PERSONA_DIR", "personas/jiang_huiyin"))
        safe_root = Path(source.get("YOLOONG_SAFE_ROOT", "."))

        return cls(
            assistant_name=source.get("YOLOONG_ASSISTANT_NAME", "江徽音"),
            user_name=source.get("YOLOONG_USER_NAME", "游龙"),
            persona_dir=(project_root / persona_dir).resolve() if not persona_dir.is_absolute() else persona_dir,
            data_dir=(project_root / data_dir).resolve() if not data_dir.is_absolute() else data_dir,
            db_path=(project_root / db_path).resolve() if not db_path.is_absolute() else db_path,
            safe_root=(project_root / safe_root).resolve() if not safe_root.is_absolute() else safe_root,
            region_profile=source.get("YOLOONG_REGION_PROFILE", "china"),
            approval_channel=source.get("YOLOONG_APPROVAL_CHANNEL", "wechat"),
            idle_interval_seconds=_int(source.get("YOLOONG_IDLE_INTERVAL_SECONDS"), 900),
            offline=_bool(source.get("YOLOONG_OFFLINE"), False),
            web_base_path=normalize_base_path(source.get("YOLOONG_WEB_BASE_PATH", "/")),
            public_url=source.get("YOLOONG_PUBLIC_URL", "https://www.yoloong.com/ai/"),
            admin_user=source.get("YOLOONG_ADMIN_USER", "yoloong"),
            admin_password_hash=source.get("YOLOONG_ADMIN_PASSWORD_HASH"),
            session_secret=source.get("YOLOONG_SESSION_SECRET"),
            deepseek=DeepSeekConfig(
                api_key=source.get("DEEPSEEK_API_KEY"),
                base_url=source.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                chat_model=source.get("DEEPSEEK_CHAT_MODEL", "deepseek-v4-pro"),
                fast_model=source.get("DEEPSEEK_FAST_MODEL", "deepseek-v4-flash"),
            ),
            dashscope=DashScopeConfig(
                api_key=source.get("DASHSCOPE_API_KEY"),
                base_url=source.get(
                    "DASHSCOPE_BASE_URL",
                    "https://dashscope.aliyuncs.com/compatible-mode/v1",
                ),
                chat_model=source.get("QWEN_CHAT_MODEL", "qwen3.6-plus"),
                vision_model=source.get("QWEN_VISION_MODEL", "qwen3-vl-plus"),
                ocr_model=source.get("QWEN_OCR_MODEL", "qwen-vl-ocr-latest"),
                translation_model=source.get("QWEN_TRANSLATION_MODEL", "qwen-mt-plus"),
            ),
        )

    def diagnostic(self) -> dict[str, object]:
        return {
            "assistant_name": self.assistant_name,
            "user_name": self.user_name,
            "persona_dir": str(self.persona_dir),
            "data_dir": str(self.data_dir),
            "db_path": str(self.db_path),
            "safe_root": str(self.safe_root),
            "region_profile": self.region_profile,
            "approval_channel": self.approval_channel,
            "offline": self.offline,
            "web_base_path": self.web_base_path,
            "public_url": self.public_url,
            "admin_user": self.admin_user,
            "admin_password_hash": "<present>" if self.admin_password_hash else "<missing>",
            "session_secret": "<present>" if self.session_secret else "<missing>",
            "deepseek_api_key": mask_secret(self.deepseek.api_key),
            "dashscope_api_key": mask_secret(self.dashscope.api_key),
            "deepseek_chat_model": self.deepseek.chat_model,
            "dashscope_vision_model": self.dashscope.vision_model,
        }


def normalize_base_path(value: str) -> str:
    value = (value or "/").strip()
    if not value.startswith("/"):
        value = "/" + value
    if len(value) > 1:
        value = value.rstrip("/")
    return value
