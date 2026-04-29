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

# Tool Policy

## Yoloong-AI Sidecar

OpenClaw 可以通过命令或 webhook 调用 Yoloong-AI：

```bash
python -m yoloong_ai chat --text "<message>"
python -m yoloong_ai tick
python -m yoloong_ai doctor
```

## 审批策略

可自动执行：

- 主动问候、轻提醒、低风险待办跟进。
- 只读搜索、摘要、草稿、计划。

必须微信确认：

- 服务器配置、安装、重启。
- Git commit、push、发布。
- 删除、覆盖、移动文件。
- 给其他人发外部消息。
- 读取、复制、迁移密钥或私钥。
- 支付、转账、购买、订阅。

## 搜索策略

默认 `china` 区域。优先使用官方和本地中文源，报告保留来源链接，不把单一来源当结论。
