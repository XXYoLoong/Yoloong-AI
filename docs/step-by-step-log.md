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

# Project Process Log

## Project Title

Yoloong-AI 24 小时在线个人微信助手

## Activity Log

### 2026-04-29 Round 1

- Request received: 构建一个基于 OpenClaw 的 24 小时在线助手，接入个人微信，具备江徽音人格、自主思考、主动消息、网络搜索、中国地区源策略、DeepSeek/Qwen 模型路由、云端安全部署、完整测试和 GitHub 推送。
- Initial repository state: `F:\YL_AI` 不是 Git 仓库，目标仓库 `Yoloong-AI` 已克隆到 `F:\YL_AI\Yoloong-AI`，初始只有 `LICENSE`。
- Persona source: 用户提供两份 `.docx` 人设文件，已抽取文本并确认江徽音核心人格、关系定位、主动陪伴、记忆连续性、表达风格、吃醋边界和禁止倾向。
- External research: 已确认 OpenClaw 官方项目为 `openclaw/openclaw`，个人微信入口使用 OpenClaw 微信插件 `@tencent-weixin/openclaw-weixin`；DeepSeek 和 DashScope 均支持 OpenAI 兼容接口。
- Security note: 本地检测到 `DEEPSEEK_API_KEY` 与 `DASHSCOPE_API_KEY` 环境变量存在，但未记录任何密钥值。
- Adjustment: 直接添加 OpenClaw 子模块时网络下载超时，已停止残留 Git 进程并改为部署脚本按需拉取/安装 OpenClaw，避免仓库被大型第三方源码卡住。
- Current action: 建立项目结构、人格资产、OpenClaw 工作区、核心代码、部署脚本和独立测试目录。

### 2026-04-29 Round 2

- Implemented: `yoloong_ai` Python 核心模块，包含配置、人格加载、DeepSeek/Qwen 模型路由、SQLite 记忆、审批策略、微信事件归一化、中国地区搜索策略、主动循环、HTTP sidecar 和 CLI。
- Implemented: `personas/jiang_huiyin` 人格资产、`openclaw/workspace` 工作区提示词、服务器部署文档、OpenClaw 安装脚本和 systemd 模板。
- Correction: 根据本机 OpenClaw CLI 与官方 WeChat 文档，将微信接入修正为 `openclaw plugins install "@tencent-weixin/openclaw-weixin"` / `openclaw channels login --channel openclaw-weixin`，删除错误的独立微信 systemd 服务。
- Correction: 根据 DashScope 官方 Qwen-VL 文档，将默认视觉模型调整为 `qwen3-vl-plus`，OCR 保持 `qwen-vl-ocr-latest`。
- Verification: 独立测试目录 `tests/` 已覆盖 18 个用例，验证模型路由、密钥隐藏、记忆生命周期、审批阻断、人格加载、微信事件、主动关怀、OpenClaw 资产和搜索解析；`python -m unittest discover -s tests -v` 通过。
- Verification: `python -m compileall yoloong_ai tests` 通过；`python -m yoloong_ai doctor` 成功识别本地 DeepSeek/DashScope 环境变量、OpenClaw CLI、npx CLI 和人格文件。
- Server access: 通过 OpenSSH 和 PuTTY/plink 多次尝试连接 `47.121.183.23:22`，TCP 端口可达，但远端在 SSH banner/密钥交换前主动关闭连接；未能进入服务器执行盘点或部署，未写入任何服务器文件。
- Publish: 已提交 `a5949b6`（`Build OpenClaw-based Yoloong assistant core`）并推送到 `origin/main`。
- Remaining caveat: 服务器部署和云端密钥写入尚未执行，原因是 SSH 入口在认证前被远端关闭；需要恢复 SSH banner/登录通道或提供新的可用访问入口后继续部署。

### 2026-04-29 Round 3

- User correction: 上一轮只交付了代码骨架，未完成完整在线体系、网页调试后台、服务器部署和微信扫码授权闭环。
- Skill mode: 已加载 `pua` 与前端设计流程，按端到端 owner 标准继续推进。
- Server audit: SSH 已恢复；服务器为 Ubuntu 24.04.4，Node 24.14.0，Python 3.12.3，Nginx 1.24.0；`yoloong-site`、`openclaw-gateway`、`astrbot`、`contest-agent-relay`、PostgreSQL 正在运行。
- Decision: 不直接删除根站点，先新增 `https://www.yoloong.com/ai/` 私有后台；旧 OpenClaw 工作区需备份后替换为江徽音工作区。若后续确认旧服务无用，再备份停用。
- Implemented: Web 控制台登录、HMAC session、PBKDF2 密码哈希、对话调试、主动 tick、审批演练、记忆读写、检索查询、状态页。
- Verification: 单元测试扩展到 23 个，全部通过；Playwright/Firefox 实际打开本地 `/ai/` 登录页，完成登录并发送“我回来了”，页面返回江徽音风格回复。

### 2026-04-29 Round 4

- Request received: 用户要求接着上个线程没有完成的任务继续完成。
- Recovery: 确认真实仓库在 `F:\YL_AI\Yoloong-AI`，外层目录不是 Git 仓库；当前未提交改动集中在服务器部署脚本和新增 `systemd/openclaw-gateway.service`。
- Current objective: 保护上轮改动，补齐部署脚本/OpenClaw gateway 服务/文档之间的一致性，运行本地验证，并在可用访问条件下继续线上部署闭环。
- Initial assumption: 上轮已完成本地 Web 后台和测试，剩余风险主要在部署脚本生成包、远端 systemd/nginx/OpenClaw 配置、微信扫码授权和最终验证。
- Finding: 线上 SSH 当前返回 `Permission denied (publickey,password)`，本地存在 `DEEPSEEK_API_KEY` 与 `DASHSCOPE_API_KEY`，但无法直接进入服务器执行部署。
- Implemented: `scripts/deploy_server.ps1` 现在拒绝脏工作区，避免 `git archive HEAD` 部署旧代码；远端会执行 `bootstrap_server.sh`、启用 `yoloong-ai.service`、调用 Nginx `/ai/` 配置脚本并做本机 health check。
- Implemented: `scripts/bootstrap_server.sh` 会安装/启用 `@tencent-weixin/openclaw-weixin`、备份旧 OpenClaw workspace、同步江徽音工作区并启动 `openclaw-gateway.service`。
- Implemented: 新增 `scripts/configure_nginx_ai.sh`，为现有 `www.yoloong.com` server block 幂等注入 `/ai/` 反向代理，`nginx -t` 失败时恢复备份。
- Implemented: `systemd/openclaw-gateway.service` 改用 `/usr/bin/env openclaw` 和 loopback bind，降低 `/usr/bin`/`/usr/local/bin` 差异导致的启动风险。
- Documentation: 更新部署说明和架构文档，明确微信插件由 OpenClaw Gateway 加载，不再单独维护微信 systemd 服务。
- Verification: `python -m unittest discover -s tests -v` 通过 27 个用例；`python -m compileall yoloong_ai tests` 通过；`bash -n scripts/bootstrap_server.sh scripts/configure_nginx_ai.sh` 通过；`deploy_server.ps1` 解析通过；`git diff --check` 通过。
- Verification: `python -m yoloong_ai doctor` 能识别人格文件、本地 OpenClaw CLI、npx CLI 和已设置的模型密钥，密钥仅以掩码形式输出。
- Verification: 以 dry-run hostname 执行 `scripts/deploy_server.ps1` 时成功触发脏工作区保护，证明不会把未提交的旧 `HEAD` 错误部署上服务器。
- Remaining blocker: 当前 SSH 到 `root@47.121.183.23` 返回 `Permission denied (publickey,password)`，因此本轮无法实际进入服务器执行部署、Nginx reload 或微信扫码登录。
- Publish: 部署闭环修复已提交并推送到 `origin/main`，本地工作区恢复干净。
- Remaining next step: 待 SSH 凭据恢复后运行 `scripts/deploy_server.ps1` 并执行 `openclaw channels login --channel openclaw-weixin` 完成扫码绑定。

### 2026-04-29 Round 5

- Request received: 用户要求按上一轮计划继续执行，重点完成 OpenClaw 个人微信扫码授权、错误落账、线上验证、测试和发布闭环。
- Recovery: 本地仓库干净，`main` 与 `origin/main` 均在 `3abafed`；部署脚本和 OpenClaw gateway 模板已包含上一轮修复。
- Blocker: 当前运行环境到 `47.121.183.23:22` 的 TCP 连接失败，SSH 在认证前超时；因此无法进入服务器清理旧登录进程、生成新的服务器侧微信二维码或确认 `/root/.openclaw` 账号凭据。
- Online verification: 公网 `https://www.yoloong.com/ai/health` 返回 `{"ok": true}`；后台登录成功，`/api/status` 显示 DeepSeek/DashScope 密钥已按掩码加载且服务非离线。
- Online verification: 已通过公网后台验证 DeepSeek 对话、主动 tick、记忆写入/检索、中国地区查询构造；审批接口使用正确 `name`/`description`/`target` payload 后生成 high 风险确认 ID，并通过 `/reject` 清空，待审批列表为空。
- Correction logged: 上一次误把“二维码已生成”接近“微信完成接入”的表达是错误边界；完成标准已补充到部署文档，必须以账号凭据、频道 configured、网关重启保留和实际微信消息链路为准。
- Verification: `python -m unittest discover -s tests -v` 通过 27 个用例；`python -m compileall yoloong_ai tests`、`git diff --check`、部署脚本语法检查和已跟踪文件敏感信息扫描均通过。
- Publish: 文档闭环记录已提交并推送到 `origin/main`，提交为 `48e3f28`。
- Current status: Yoloong-AI Web 后台在线，微信扫码授权未完成；阻塞原因是当前网络无法访问服务器 SSH，而不是 OpenClaw 或 API 已完成失败。

### 2026-04-29 Round 6

- Request received: 用户已恢复服务器 TCP/SSH，要求继续完成微信授权闭环。
- Recovery: `47.121.183.23:22` 已恢复连通，root SSH 登录成功；旧微信二维码登录进程已过期退出，无账号凭据落盘。
- WeChat binding: 重新运行 `openclaw channels login --channel openclaw-weixin --verbose` 并生成新二维码；用户扫码后服务器日志显示“已将此 OpenClaw 连接到微信”。
- Verification: `/root/.openclaw/openclaw-weixin/accounts.json` 已出现账号索引，账号凭据文件中 token 已存在；`openclaw channels list` 显示 `openclaw-weixin default: configured, enabled`。
- Gateway repair: 发现旧孤立 `openclaw-gateway` 进程占用 `18789` 导致 systemd 反复重启；已停服务、清理旧 PID，并将 gateway service 固定为 `openclaw gateway run --port 18789 --bind loopback --allow-unconfigured --force`。
- WeChat delivery: 已通过 `openclaw message send --channel openclaw-weixin` 向本人微信发送联调消息，OpenClaw 返回 messageId，出站链路验证通过。
- Online verification: 公网 `/ai/health`、后台登录、`/api/status`、DeepSeek 对话、主动 tick、高风险审批、记忆写入/检索和中国地区查询构造均通过；测试审批已通过 `/reject` 清空，待审批列表为空。
- Local verification: `python -m unittest discover -s tests -v` 通过 27 个用例；`python -m compileall yoloong_ai tests`、`git diff --check` 和已跟踪文件敏感信息扫描均通过。
