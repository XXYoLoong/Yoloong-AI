#!/usr/bin/env bash
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

set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/yoloong-ai}"
ENV_DIR="${ENV_DIR:-/etc/yoloong-ai}"
ENV_FILE="$ENV_DIR/yoloong-ai.env"
OPENCLAW_HOME="${OPENCLAW_HOME:-/root/.openclaw}"
OPENCLAW_GATEWAY_PORT="${OPENCLAW_GATEWAY_PORT:-18789}"
BACKUP_ROOT="${BACKUP_ROOT:-/root/yoloong-ai-backups}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

apt-get update
apt-get install -y git curl python3 python3-venv python3-pip nodejs npm

mkdir -p "$APP_ROOT/app" "$APP_ROOT/data" "$APP_ROOT/logs" "$APP_ROOT/openclaw-workspace" "$ENV_DIR"
chmod 700 "$ENV_DIR"
touch "$ENV_FILE"
chmod 600 "$ENV_FILE"

if command -v npm >/dev/null 2>&1; then
  npm install -g n
  n 24 || true
  npm install -g openclaw@latest
  if command -v openclaw >/dev/null 2>&1; then
    openclaw plugins install "@tencent-weixin/openclaw-weixin" || true
    openclaw config set plugins.entries.openclaw-weixin.enabled true || true
  fi
  npx -y @tencent-weixin/openclaw-weixin-cli install || true
fi

mkdir -p "$OPENCLAW_HOME" "$BACKUP_ROOT"

python3 - <<PY
import json
from pathlib import Path

home = Path("$OPENCLAW_HOME")
config_path = home / "openclaw.json"
if config_path.exists():
    data = json.loads(config_path.read_text(encoding="utf-8"))
else:
    data = {}

gateway = data.setdefault("gateway", {})
gateway["port"] = int("$OPENCLAW_GATEWAY_PORT")
gateway["mode"] = "local"
gateway["bind"] = "loopback"
gateway.setdefault("auth", {})["mode"] = "token"
gateway.setdefault("tailscale", {})["mode"] = "off"

plugins = data.setdefault("plugins", {})
entries = plugins.setdefault("entries", {})
entries.pop("qwen-portal-auth", None)
entries.setdefault("openclaw-weixin", {})["enabled"] = True
plugins["allow"] = ["openclaw-weixin"]

agents = data.setdefault("agents", {})
defaults = agents.setdefault("defaults", {})
defaults["workspace"] = str(home / "workspace")

config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

WEIXIN_MANIFEST="$OPENCLAW_HOME/extensions/openclaw-weixin/openclaw.plugin.json"
if [ -f "$WEIXIN_MANIFEST" ]; then
  python3 - <<PY
import json
from pathlib import Path

p = Path("$WEIXIN_MANIFEST")
data = json.loads(p.read_text(encoding="utf-8"))
data["channelConfigs"] = {
    "openclaw-weixin": {
        "label": "openclaw-weixin",
        "description": "Weixin personal-account channel using QR login and long-poll messaging.",
        "schema": {
            "\$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "name": {"type": "string"},
                "enabled": {"type": "boolean"},
                "baseUrl": {"type": "string", "default": "https://ilinkai.weixin.qq.com"},
                "cdnBaseUrl": {"type": "string", "default": "https://novac2c.cdn.weixin.qq.com/c2c"},
                "routeTag": {"anyOf": [{"type": "number"}, {"type": "string"}]},
                "botAgent": {"type": "string"},
                "channelConfigUpdatedAt": {"type": "string"},
                "accounts": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "name": {"type": "string"},
                            "enabled": {"type": "boolean"},
                            "baseUrl": {"type": "string", "default": "https://ilinkai.weixin.qq.com"},
                            "cdnBaseUrl": {"type": "string", "default": "https://novac2c.cdn.weixin.qq.com/c2c"},
                            "routeTag": {"anyOf": [{"type": "number"}, {"type": "string"}]},
                            "botAgent": {"type": "string"},
                        },
                    },
                },
            },
        },
    }
}
p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
fi

if [ -d "$REPO_ROOT/openclaw/workspace" ]; then
  if [ -d "$OPENCLAW_HOME/workspace" ] && [ -n "$(find "$OPENCLAW_HOME/workspace" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
    timestamp="$(date +%Y%m%d-%H%M%S)"
    cp -a "$OPENCLAW_HOME/workspace" "$BACKUP_ROOT/openclaw-workspace-$timestamp"
  fi
  mkdir -p "$OPENCLAW_HOME/workspace"
  cp -a "$REPO_ROOT/openclaw/workspace/." "$OPENCLAW_HOME/workspace/"
  touch "$OPENCLAW_HOME/workspace/.yoloong-managed"
fi

if [ -f "$REPO_ROOT/systemd/openclaw-gateway.service" ]; then
  cp "$REPO_ROOT/systemd/openclaw-gateway.service" /etc/systemd/system/openclaw-gateway.service
  systemctl daemon-reload
  systemctl enable --now openclaw-gateway.service || true
  systemctl restart openclaw-gateway.service || true
fi

if [ ! -s "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<EOF
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-}
DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY:-}
YOLOONG_DB_PATH=$APP_ROOT/data/yoloong.sqlite3
YOLOONG_DATA_DIR=$APP_ROOT/data
YOLOONG_SAFE_ROOT=$APP_ROOT
YOLOONG_PERSONA_DIR=$APP_ROOT/app/personas/jiang_huiyin
YOLOONG_REGION_PROFILE=china
YOLOONG_APPROVAL_CHANNEL=wechat
YOLOONG_ASSISTANT_NAME=江徽音
YOLOONG_USER_NAME=游龙
YOLOONG_WEB_BASE_PATH=/ai
YOLOONG_PUBLIC_URL=https://www.yoloong.com/ai/
YOLOONG_ADMIN_USER=${YOLOONG_ADMIN_USER:-yoloong}
YOLOONG_ADMIN_PASSWORD_HASH=${YOLOONG_ADMIN_PASSWORD_HASH:-}
YOLOONG_SESSION_SECRET=${YOLOONG_SESSION_SECRET:-}
EOF
fi
chmod 600 "$ENV_FILE"

echo "Server bootstrap complete at $APP_ROOT."
