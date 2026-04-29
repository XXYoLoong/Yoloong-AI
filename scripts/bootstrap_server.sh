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
  npx -y @tencent-weixin/openclaw-weixin-cli install
fi

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
EOF
chmod 600 "$ENV_FILE"

echo "Server bootstrap complete at $APP_ROOT."
