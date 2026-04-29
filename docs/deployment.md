<!--
Copyright 2026 Jiacheng Ni

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# 部署说明

## 本地验证

```powershell
python -m yoloong_ai doctor
python -m unittest discover -s tests
```

## 一键部署

部署脚本会打包当前 `HEAD`、生成 root-only env 文件、上传到服务器、执行 `scripts/bootstrap_server.sh`、安装/更新 OpenClaw 微信插件、替换 OpenClaw 工作区、启动 `yoloong-ai.service` 和 `openclaw-gateway.service`，并为现有 `www.yoloong.com` Nginx server block 注入 `/ai/` 反向代理。

```powershell
$env:YOLOONG_SERVER_HOST="47.121.183.23"
$env:DEEPSEEK_API_KEY="..."
$env:DASHSCOPE_API_KEY="..."
.\scripts\deploy_server.ps1
```

脚本故意拒绝部署脏工作区，因为它使用 `git archive HEAD` 打包；部署前先完成测试、提交并推送，避免把旧版本发上服务器。

## 服务器准备

Ubuntu 24.04 推荐：

```bash
sudo apt-get update
sudo apt-get install -y git curl python3 python3-venv nodejs npm
sudo npm install -g n
sudo n 24
sudo npm install -g openclaw@latest
npx -y @tencent-weixin/openclaw-weixin-cli install
```

## 目录与密钥

```bash
sudo mkdir -p /opt/yoloong-ai/app /opt/yoloong-ai/data /opt/yoloong-ai/logs /etc/yoloong-ai
sudo chmod 700 /etc/yoloong-ai
sudo install -m 600 /dev/null /etc/yoloong-ai/yoloong-ai.env
```

`/etc/yoloong-ai/yoloong-ai.env` 示例：

```bash
DEEPSEEK_API_KEY=...
DASHSCOPE_API_KEY=...
YOLOONG_DB_PATH=/opt/yoloong-ai/data/yoloong.sqlite3
YOLOONG_DATA_DIR=/opt/yoloong-ai/data
YOLOONG_SAFE_ROOT=/opt/yoloong-ai
YOLOONG_REGION_PROFILE=china
YOLOONG_APPROVAL_CHANNEL=wechat
YOLOONG_WEB_BASE_PATH=/ai
YOLOONG_PUBLIC_URL=https://www.yoloong.com/ai/
YOLOONG_ADMIN_USER=yoloong
YOLOONG_ADMIN_PASSWORD_HASH=...
YOLOONG_SESSION_SECRET=...
```

生成后台账号密码和哈希：

```bash
python3 -m yoloong_ai generate-admin --user yoloong
```

Web 调试后台默认挂载到：

```text
https://www.yoloong.com/ai/
```

## OpenClaw 微信绑定

```bash
openclaw channels login --channel openclaw-weixin
```

手机扫码完成后，按 OpenClaw 配对提示批准本人微信账号；部署脚本已把 `openclaw/workspace` 同步到 `/root/.openclaw/workspace`，并会在替换前备份旧工作区到 `/root/yoloong-ai-backups/`。

微信绑定的完成标准不是“二维码已生成”，而是同时满足：

- `/root/.openclaw` 下出现 `openclaw-weixin` 账号凭据文件。
- `openclaw channels list` 或频道状态显示微信账号已 configured。
- `openclaw-gateway.service` 重启后登录态仍保留。
- 至少完成一次微信入站或出站链路验证。

如果当前网络无法连接服务器 `22` 端口，只能验证公网 `/ai/` 后台，不能生成服务器侧二维码，也不能判定微信已接入。

## systemd

复制模板：

```bash
sudo cp systemd/yoloong-ai.service /etc/systemd/system/yoloong-ai.service
sudo systemctl daemon-reload
sudo systemctl enable --now yoloong-ai.service
sudo systemctl status yoloong-ai.service
```

OpenClaw Gateway 使用 `systemd/openclaw-gateway.service`，由 `scripts/bootstrap_server.sh` 自动复制并启动。微信插件作为 OpenClaw channel plugin 由 Gateway 加载，不需要单独的微信 systemd 服务。

## Nginx

`scripts/configure_nginx_ai.sh` 会在目标 server block 中加入：

```nginx
location /ai/ {
    proxy_pass http://127.0.0.1:8721;
}
```

脚本会先备份命中的 Nginx 配置，执行 `nginx -t`，通过后 reload；若测试失败，会恢复备份并中止。
