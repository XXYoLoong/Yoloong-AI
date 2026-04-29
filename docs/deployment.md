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

手机扫码完成后，把 `openclaw/workspace` 同步到 OpenClaw 工作区。

## systemd

复制模板：

```bash
sudo cp systemd/yoloong-ai.service /etc/systemd/system/yoloong-ai.service
sudo systemctl daemon-reload
sudo systemctl enable --now yoloong-ai.service
sudo systemctl status yoloong-ai.service
```

OpenClaw 和微信插件服务同理按实际安装路径配置。
