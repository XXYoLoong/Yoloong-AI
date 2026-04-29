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

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil

from .autonomy import AutonomousAssistant
from .config import RuntimeConfig
from .memory import MemoryStore
from .models import ModelRouter
from .permissions import ApprovalPolicy
from .persona import Persona
from .server import run_server


def build_assistant(config: RuntimeConfig) -> AutonomousAssistant:
    memory = MemoryStore(config.db_path)
    persona = Persona.load(config.persona_dir, name=config.assistant_name, user_name=config.user_name)
    router = ModelRouter(config)
    policy = ApprovalPolicy(config.safe_root, owner_aliases={"user", config.user_name})
    return AutonomousAssistant(config, memory, persona, router, policy)


def cmd_doctor(args: argparse.Namespace) -> int:
    config = RuntimeConfig.from_env(root=Path.cwd())
    report = config.diagnostic()
    report["persona_files_ok"] = all((config.persona_dir / name).exists() for name in (
        "SOUL.md",
        "STYLE.md",
        "BOUNDARIES.md",
        "MEMORY_SCHEMA.md",
    ))
    report["openclaw_cli"] = shutil.which("openclaw") or "<missing>"
    report["npx_cli"] = shutil.which("npx") or "<missing>"
    report["wechat_channel"] = "openclaw-weixin"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def cmd_init_db(args: argparse.Namespace) -> int:
    path = Path(args.db)
    memory = MemoryStore(path)
    memory.close()
    print(json.dumps({"ok": True, "db": str(path)}, ensure_ascii=False))
    return 0


def cmd_chat(args: argparse.Namespace) -> int:
    env_config = RuntimeConfig.from_env(root=Path.cwd())
    config = env_config
    if args.offline:
        config = RuntimeConfig.from_env(
            env={**dict(os.environ), "YOLOONG_OFFLINE": "1"},
            root=Path.cwd(),
        )
    assistant = build_assistant(config)
    try:
        output = assistant.handle_user_message(args.text)
        print(output.text)
    finally:
        assistant.close()
    return 0


def cmd_tick(args: argparse.Namespace) -> int:
    config = RuntimeConfig.from_env(root=Path.cwd())
    if args.offline:
        config = RuntimeConfig.from_env(
            env={**dict(os.environ), "YOLOONG_OFFLINE": "1"},
            root=Path.cwd(),
        )
    assistant = build_assistant(config)
    now = datetime.fromisoformat(args.now) if args.now else None
    try:
        output = assistant.tick(now)
        print(output.text)
    finally:
        assistant.close()
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    config = RuntimeConfig.from_env(root=Path.cwd())

    def factory() -> AutonomousAssistant:
        return build_assistant(config)

    run_server(args.host, args.port, factory)
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="yoloong-ai")
    sub = root.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor")
    doctor.set_defaults(func=cmd_doctor)

    init_db = sub.add_parser("init-db")
    init_db.add_argument("--db", default=".runtime/yoloong.sqlite3")
    init_db.set_defaults(func=cmd_init_db)

    chat = sub.add_parser("chat")
    chat.add_argument("--text", required=True)
    chat.add_argument("--offline", action="store_true")
    chat.set_defaults(func=cmd_chat)

    tick = sub.add_parser("tick")
    tick.add_argument("--now")
    tick.add_argument("--offline", action="store_true")
    tick.set_defaults(func=cmd_tick)

    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8721)
    serve.set_defaults(func=cmd_serve)

    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return int(args.func(args))
