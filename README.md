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

# Yoloong-AI

Yoloong-AI 是一个围绕 OpenClaw 构建的 24 小时在线个人助手工程。OpenClaw 负责多渠道网关和个人微信入口，Yoloong-AI 负责人格稳定、主动决策、模型路由、长期记忆、权限审批、网络检索和部署运维。

当前设计目标：

- 个人微信接入：使用 OpenClaw 官方微信插件 `@tencent-weixin/openclaw-weixin`，由手机扫码完成授权。
- 对话模型：DeepSeek 优先负责中文对话、规划、推理和日常陪伴。
- 多模态模型：DashScope/Qwen 优先负责视觉、OCR、翻译、图片理解等场景。
- 人格：默认加载 `personas/jiang_huiyin`，形成“江徽音”式的温润、细腻、主动陪伴风格。
- 自主性：空闲时会生成低风险主动关怀、日报、待办跟进、项目巡检建议；涉及核心操作时必须向用户发起微信确认。
- 中国场景：网络检索和报告默认启用中国地区源策略，优先使用 `gov.cn`、官方媒体和中国本地服务源。

## 快速使用

```powershell
python -m yoloong_ai doctor
python -m yoloong_ai init-db --db .runtime/yoloong.sqlite3
python -m yoloong_ai chat --offline --text "我回来了"
python -m yoloong_ai generate-admin --user yoloong
python -m unittest discover -s tests
```

## 关键目录

- `yoloong_ai/`：助手核心代码。
- `personas/jiang_huiyin/`：江徽音人格资产。
- `openclaw/workspace/`：可复制到 OpenClaw 工作区的提示词与工具约束。
- `config/`：运行配置模板。
- `scripts/`：本地、服务器和 OpenClaw 部署脚本。
- `systemd/`：Ubuntu 服务器 24 小时守护进程模板。
- `tests/`：独立测试目录，覆盖模型路由、记忆、权限、人格、微信事件和自主循环。
- `docs/system-plan.md`：完整线上体系规划。
- `docs/server-audit.md`：服务器审计摘要。
- `docs/`：架构、部署和过程日志。

## 密钥

本仓库不提交任何真实密钥。运行时只从环境变量读取：

- `DEEPSEEK_API_KEY`
- `DASHSCOPE_API_KEY`

服务器部署时使用 `scripts/bootstrap_server.sh` 创建 root-only 的 `/etc/yoloong-ai/yoloong-ai.env`，文件权限为 `600`。

## OpenClaw 微信入口

个人微信入口通过 OpenClaw 插件完成：

```bash
npm install -g openclaw@latest
npx -y @tencent-weixin/openclaw-weixin-cli install
openclaw channels login --channel openclaw-weixin
```

扫码登录完成后，把 `openclaw/workspace` 中的资产复制到 OpenClaw workspace，或运行部署脚本自动同步。

## 验证

本项目不把“能启动”当成验证。核心逻辑必须通过独立测试目录：

```bash
python -m unittest discover -s tests
```

联网搜索、真实模型调用、个人微信扫码属于外部集成测试，默认不会在单元测试中调用真实服务。
