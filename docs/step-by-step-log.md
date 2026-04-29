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
