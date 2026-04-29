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

# 服务器审计摘要

审计时间：2026-04-29

## 基础环境

- 主机：阿里云 ECS，Ubuntu 24.04.4 LTS，Linux 6.8.0-88。
- 内存：3.4GiB，无 swap；常驻服务需要克制。
- 磁盘：根分区 40GiB，已用约 7.3GiB。
- Node.js：24.14.0。
- Python：3.12.3。
- Nginx：1.24.0。

## 现有服务

- `yoloong-site.service`：Node 站点，`/var/www/yoloong.com/current/server.js`，端口 `8080`，用户 `www-data`。
- `openclaw-gateway.service`：旧 OpenClaw Gateway，`/usr/bin/openclaw gateway --port 18789`，工作目录 `/root`。
- `astrbot.service`：AstrBot，目录 `/opt/AstrBot`，公开监听 `0.0.0.0:6185`。
- `contest-agent-relay.service`：Uvicorn relay，监听 `127.0.0.1:8210`，nginx 已代理 `/contest-agent-relay/`。
- `postgresql@16-main.service`：本地 PostgreSQL，仅本机监听。

## Nginx

- `www.yoloong.com` 和 `yoloong.com` 已启用 HTTPS。
- 根路径代理到 `127.0.0.1:8080`。
- 已有 `/contest-agent-relay/` 代理到 `127.0.0.1:8210`。
- 默认域名 `_` 返回 `444`。
- Nginx 配置测试通过。

## OpenClaw

- 服务器版本：`2026.3.13`，本地版本：`2026.4.1`。
- 当前 channel 为空，还没有微信接入。
- 当前 OpenClaw 配置使用 `qwen-portal` OAuth，主模型为 `qwen-portal/coder-model`。
- Gateway token 存在于 `/root/.openclaw/openclaw.json`，不应进入仓库或日志。
- 工作区文件存在：`SOUL.md`、`AGENTS.md`、`TOOLS.md`、`USER.md` 等，但属于旧学习结果，应备份后替换。

## 处置结论

- 不直接删除根站点，先新增 `/ai/` 调试后台，降低对现有站点的影响。
- 旧 OpenClaw 工作区需要替换；替换前备份 `/root/.openclaw`。
- `openclaw-gateway.service` 可沿用服务名，但应升级 OpenClaw 并更新工作区。
- 若后续确认旧 `astrbot`、`contest-agent-relay` 不再需要，可在备份后停用，释放内存和端口。
