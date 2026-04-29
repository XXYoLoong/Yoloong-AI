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
    [string]$RemoteRoot = "/opt/yoloong-ai",
    [string]$AdminUser = "yoloong",
    [string]$AdminPassword = $env:YOLOONG_ADMIN_PASSWORD
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

if (-not $HostName) {
    throw "Set YOLOONG_SERVER_HOST or pass -HostName."
}
if (-not $env:DEEPSEEK_API_KEY -or -not $env:DASHSCOPE_API_KEY) {
    throw "DEEPSEEK_API_KEY and DASHSCOPE_API_KEY must exist in the local environment."
}

if (-not $AdminPassword) {
    $generated = python -m yoloong_ai generate-admin --user $AdminUser | ConvertFrom-Json
    $AdminPassword = $generated.admin_password
} else {
    $generated = python -m yoloong_ai generate-admin --user $AdminUser --password $AdminPassword | ConvertFrom-Json
}

$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
$runtime = Join-Path $repo ".runtime"
$package = Join-Path $runtime "deploy-yoloong-ai.tar.gz"
$secretFile = Join-Path $runtime "yoloong-ai.env"
New-Item -ItemType Directory -Force -Path $runtime | Out-Null

$dirty = git -C $repo status --porcelain
if ($dirty) {
    throw "Refusing to deploy a dirty worktree because git archive packages HEAD only. Commit or stash changes first."
}

git -C $repo archive --format=tar.gz -o $package HEAD

$envContent = @"
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
YOLOONG_WEB_BASE_PATH=/ai
YOLOONG_PUBLIC_URL=https://www.yoloong.com/ai/
YOLOONG_ADMIN_USER=$AdminUser
YOLOONG_ADMIN_PASSWORD_HASH=$($generated.admin_password_hash)
YOLOONG_SESSION_SECRET=$($generated.session_secret)
"@
[IO.File]::WriteAllText($secretFile, $envContent, [Text.UTF8Encoding]::new($false))

try {
    scp $package "${User}@${HostName}:/tmp/yoloong-ai.tar.gz"
    scp $secretFile "${User}@${HostName}:/tmp/yoloong-ai.env"

    $remoteScript = @'
set -euo pipefail

remote_root="$1"

mkdir -p "$remote_root/data" "$remote_root/logs" /etc/yoloong-ai
rm -rf "$remote_root/app"
mkdir -p "$remote_root/app"
tar -xzf /tmp/yoloong-ai.tar.gz -C "$remote_root/app"
install -m 600 /tmp/yoloong-ai.env /etc/yoloong-ai/yoloong-ai.env

cd "$remote_root/app"
APP_ROOT="$remote_root" bash scripts/bootstrap_server.sh

cp "$remote_root/app/systemd/yoloong-ai.service" /etc/systemd/system/yoloong-ai.service
systemctl daemon-reload
systemctl enable --now yoloong-ai.service
systemctl restart yoloong-ai.service

if command -v nginx >/dev/null 2>&1; then
  bash "$remote_root/app/scripts/configure_nginx_ai.sh"
fi

systemctl is-active yoloong-ai.service
systemctl is-active openclaw-gateway.service || true
curl -fsS http://127.0.0.1:8721/ai/health >/dev/null

rm -f /tmp/yoloong-ai.tar.gz /tmp/yoloong-ai.env
'@
    $remoteScript | ssh "${User}@${HostName}" "bash -s -- '$RemoteRoot'"
} finally {
    if (Test-Path $package) {
        Remove-Item -LiteralPath $package -Force
    }
    if (Test-Path $secretFile) {
        Remove-Item -LiteralPath $secretFile -Force
    }
}

Write-Host "Deployment finished for $HostName"
Write-Host "Admin user: $AdminUser"
Write-Host "Admin password: $AdminPassword"
Write-Host "Next: ssh ${User}@${HostName} 'openclaw channels login --channel openclaw-weixin' and scan the QR code with WeChat."
