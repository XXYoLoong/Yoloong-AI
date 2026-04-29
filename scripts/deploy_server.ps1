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

param(
    [string]$HostName = $env:YOLOONG_SERVER_HOST,
    [string]$User = "root",
    [string]$RemoteRoot = "/opt/yoloong-ai"
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

if (-not $HostName) {
    throw "Set YOLOONG_SERVER_HOST or pass -HostName."
}
if (-not $env:DEEPSEEK_API_KEY -or -not $env:DASHSCOPE_API_KEY) {
    throw "DEEPSEEK_API_KEY and DASHSCOPE_API_KEY must exist in the local environment."
}

$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
$runtime = Join-Path $repo ".runtime"
$package = Join-Path $runtime "deploy-yoloong-ai.tar.gz"
New-Item -ItemType Directory -Force -Path $runtime | Out-Null

git -C $repo archive --format=tar.gz -o $package HEAD
scp $package "${User}@${HostName}:/tmp/yoloong-ai.tar.gz"
ssh "${User}@${HostName}" "mkdir -p '$RemoteRoot/app' && tar -xzf /tmp/yoloong-ai.tar.gz -C '$RemoteRoot/app'"
ssh "${User}@${HostName}" "cd '$RemoteRoot/app' && bash scripts/bootstrap_server.sh"

$secretFile = Join-Path $runtime "yoloong-ai.env"
@"
DEEPSEEK_API_KEY=$env:DEEPSEEK_API_KEY
DASHSCOPE_API_KEY=$env:DASHSCOPE_API_KEY
YOLOONG_DB_PATH=$RemoteRoot/data/yoloong.sqlite3
YOLOONG_DATA_DIR=$RemoteRoot/data
YOLOONG_SAFE_ROOT=$RemoteRoot
YOLOONG_PERSONA_DIR=$RemoteRoot/app/personas/jiang_huiyin
YOLOONG_REGION_PROFILE=china
YOLOONG_APPROVAL_CHANNEL=wechat
YOLOONG_ASSISTANT_NAME=江徽音
YOLOONG_USER_NAME=游龙
"@ | Set-Content -LiteralPath $secretFile -Encoding utf8NoBOM
scp $secretFile "${User}@${HostName}:/etc/yoloong-ai/yoloong-ai.env"
ssh "${User}@${HostName}" "chmod 600 /etc/yoloong-ai/yoloong-ai.env"

ssh "${User}@${HostName}" "cp '$RemoteRoot/app/systemd/yoloong-ai.service' /etc/systemd/system/yoloong-ai.service && systemctl daemon-reload && systemctl enable --now yoloong-ai.service"

Remove-Item -LiteralPath $package -Force
Remove-Item -LiteralPath $secretFile -Force
Write-Host "Deployment finished for $HostName"
