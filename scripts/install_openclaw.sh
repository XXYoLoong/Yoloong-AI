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

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required before installing OpenClaw." >&2
  exit 1
fi

node_major="$(node -p "process.versions.node.split('.')[0]" 2>/dev/null || echo 0)"
if [ "$node_major" -lt 24 ]; then
  echo "Node.js 24+ is recommended for OpenClaw. Current major: $node_major" >&2
fi

npm install -g openclaw@latest
npx -y @tencent-weixin/openclaw-weixin-cli install

echo "OpenClaw and WeChat plugin installed."
echo "Next: run openclaw onboard, then openclaw channels login --channel openclaw-weixin."
