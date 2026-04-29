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

# Yoloong-AI 完整体系规划

## 目标

构建一个 24 小时在线的个人助手系统：江徽音人格常驻、个人微信接入、网页调试后台、自主思考、权限审批、长期记忆、网络检索、中国地区报告、服务器守护和可回归测试。

## 新系统边界

- `https://www.yoloong.com/ai/`：只允许游龙本人登录的 Web 调试控制台。
- `127.0.0.1:8721`：Yoloong-AI sidecar，提供登录、对话、主动循环、审批、记忆、检索和 OpenClaw webhook。
- `/opt/yoloong-ai/app`：项目代码。
- `/opt/yoloong-ai/data`：SQLite 记忆库和运行数据。
- `/etc/yoloong-ai/yoloong-ai.env`：root-only 运行密钥、模型密钥、后台账号密码哈希和 session secret。
- `/root/.openclaw/workspace`：OpenClaw 工作区，替换为江徽音 SOUL/AGENTS/TOOLS。
- `openclaw-gateway.service`：继续负责 OpenClaw Gateway 与微信 channel。

## 模块体系

| 模块 | 职责 | 风险策略 |
| --- | --- | --- |
| 江徽音人格 | 稳定语言风格、关系感、主动陪伴 | 只保存摘要资产，不保存原始 Word 全文 |
| 模型路由 | DeepSeek 文本对话；Qwen 多模态/OCR/翻译 | 密钥只在环境变量和 root-only env 文件 |
| Web 控制台 | 在线调试、状态、记忆、审批、主动 tick | PBKDF2 密码哈希 + HMAC session cookie |
| 主动循环 | 按时间和记忆生成主动关怀与任务跟进 | 低风险可执行，核心动作必须确认 |
| 审批系统 | 拦截 Git、服务器、删除、密钥、外发消息等动作 | 生成 `/approve` / `/reject` 确认语句 |
| OpenClaw | 微信入口、Gateway、渠道消息 | 工作区替换为 Yoloong-AI 指令 |
| Nginx | `/ai/` 反向代理，不影响根站点 | 修改前备份配置，`nginx -t` 后 reload |

## 迁移策略

1. 备份旧配置：
   - `/etc/nginx/conf.d`
   - `/etc/systemd/system/*openclaw*`
   - `/root/.openclaw`
   - `/var/www/yoloong.com/current`
2. 不直接删除现有根站点，先把 `/ai/` 独立上线，验证稳定后再决定是否整站重构。
3. 更新 OpenClaw 到新版，安装微信插件。
4. 用本仓库的 `openclaw/workspace` 替换旧 OpenClaw workspace。
5. 启动 `yoloong-ai.service`，验证本机 health、网页登录、API、nginx 代理。
6. 执行 `openclaw channels login --channel openclaw-weixin`，等待游龙扫码授权。
7. 扫码后验证微信消息进入 Yoloong-AI。

## 验收标准

- 单元测试全部通过。
- `https://www.yoloong.com/ai/` 未登录返回登录页。
- 正确账号密码登录后能进入控制台。
- 控制台对话调试返回江徽音风格回复。
- 主动 tick、审批演练、记忆读写、检索查询 API 正常。
- Nginx `nginx -t` 成功，`systemctl is-active yoloong-ai` 成功。
- OpenClaw Gateway 运行，微信 channel 扫码绑定完成。
- 代码提交并推送 GitHub。
