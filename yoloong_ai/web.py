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

from __future__ import annotations

import html
import json

from .config import RuntimeConfig


def url(config: RuntimeConfig, path: str) -> str:
    base = config.web_base_path
    if not path.startswith("/"):
        path = "/" + path
    if base == "/":
        return path
    return base + path


def login_page(config: RuntimeConfig, error: str = "") -> str:
    error_html = f"<p class='error'>{html.escape(error)}</p>" if error else ""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>江徽音控制台登录</title>
  <style>{CSS}</style>
</head>
<body class="login-shell">
  <main class="login-panel">
    <p class="eyebrow">Yoloong-AI</p>
    <h1>江徽音控制台</h1>
    <p class="lead">只允许游龙本人进入。登录后可以在线调试对话、主动思考、审批、记忆和检索链路。</p>
    {error_html}
    <form method="post" action="{url(config, '/login')}">
      <label>账号<input name="username" autocomplete="username" required /></label>
      <label>密码<input name="password" type="password" autocomplete="current-password" required /></label>
      <button type="submit">进入控制台</button>
    </form>
  </main>
</body>
</html>"""


def dashboard_page(config: RuntimeConfig) -> str:
    state = {
        "base": config.web_base_path,
        "publicUrl": config.public_url,
        "assistant": config.assistant_name,
        "user": config.user_name,
    }
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>江徽音控制台</title>
  <style>{CSS}</style>
</head>
<body>
  <div class="app">
    <aside class="side">
      <div>
        <p class="eyebrow">Yoloong-AI</p>
        <h1>江徽音</h1>
        <p class="muted">在线调试台 · 只读默认安全 · 核心动作微信确认</p>
      </div>
      <nav>
        <a href="#chat">对话</a>
        <a href="#autonomy">主动循环</a>
        <a href="#approval">审批</a>
        <a href="#memory">记忆</a>
        <a href="#research">检索</a>
        <a href="#system">系统</a>
      </nav>
      <a class="logout" href="{url(config, '/logout')}">退出</a>
    </aside>
    <main class="workspace">
      <section class="topline">
        <div>
          <p class="eyebrow">Protected Console</p>
          <h2>线上调试与自主决策面板</h2>
        </div>
        <button id="refreshStatus">刷新状态</button>
      </section>
      <section id="chat" class="pane two">
        <div class="module">
          <h3>对话调试</h3>
          <div id="chatLog" class="log"></div>
          <form id="chatForm" class="row">
            <input id="chatInput" placeholder="给江徽音发一条测试消息" />
            <button>发送</button>
          </form>
        </div>
        <div id="autonomy" class="module">
          <h3>主动思考</h3>
          <p class="muted">手动触发一次空闲循环，验证早午晚问候、待办跟进和风险分类。</p>
          <button id="tickButton">触发 tick</button>
          <pre id="tickOutput"></pre>
        </div>
      </section>
      <section id="approval" class="pane two">
        <div class="module">
          <h3>高风险动作演练</h3>
          <p class="muted">生成一条需要微信确认的动作，不会真正执行。</p>
          <button id="proposePush">模拟 GitHub 推送审批</button>
          <pre id="approvalOutput"></pre>
        </div>
        <div class="module">
          <h3>待审批</h3>
          <button id="loadApprovals">读取审批队列</button>
          <div id="approvalList" class="list"></div>
        </div>
      </section>
      <section id="memory" class="pane two">
        <div class="module">
          <h3>写入记忆</h3>
          <form id="memoryForm" class="stack">
            <input id="memoryKey" placeholder="key，例如 routine.breakfast" />
            <textarea id="memoryValue" placeholder="记忆内容"></textarea>
            <button>保存记忆</button>
          </form>
        </div>
        <div class="module">
          <h3>记忆检索</h3>
          <form id="memorySearchForm" class="row">
            <input id="memoryQuery" placeholder="搜索关键词" />
            <button>搜索</button>
          </form>
          <div id="memoryResults" class="list"></div>
        </div>
      </section>
      <section id="research" class="pane">
        <div class="module">
          <h3>中国地区检索策略</h3>
          <form id="researchForm" class="row">
            <input id="researchTopic" placeholder="例如：全国天气预警、安徽政策、AI 开源项目" />
            <button>生成检索查询</button>
          </form>
          <div id="researchResults" class="list"></div>
        </div>
      </section>
      <section id="system" class="pane">
        <div class="module">
          <h3>系统状态</h3>
          <pre id="statusBox"></pre>
        </div>
      </section>
    </main>
  </div>
  <script>window.YOLOONG = {json.dumps(state, ensure_ascii=False)};</script>
  <script>{JS}</script>
</body>
</html>"""


CSS = """
:root {
  color-scheme: light;
  --ink: #17201d;
  --muted: #68736d;
  --line: #d8dfd8;
  --surface: #f7f5ef;
  --panel: #ffffff;
  --accent: #176b5b;
  --warn: #b54f35;
  --soft: #e8eee7;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: var(--surface); }
button, input, textarea { font: inherit; }
button { border: 0; background: var(--accent); color: white; padding: 10px 14px; border-radius: 7px; cursor: pointer; min-height: 40px; }
button:hover { filter: brightness(.94); }
input, textarea { width: 100%; border: 1px solid var(--line); border-radius: 7px; padding: 11px 12px; background: white; color: var(--ink); }
textarea { min-height: 92px; resize: vertical; }
pre { white-space: pre-wrap; overflow: auto; background: #101816; color: #e9f4ef; padding: 14px; border-radius: 7px; min-height: 92px; }
.login-shell { min-height: 100svh; display: grid; place-items: center; padding: 24px; background: radial-gradient(circle at 20% 20%, #dde8de 0, transparent 34%), var(--surface); }
.login-panel { width: min(520px, 100%); }
.login-panel h1 { margin: 0 0 12px; font-size: clamp(34px, 8vw, 68px); line-height: .95; }
.login-panel form { display: grid; gap: 14px; margin-top: 28px; }
.login-panel label { display: grid; gap: 7px; color: var(--muted); }
.lead { color: var(--muted); line-height: 1.7; max-width: 44ch; }
.error { color: var(--warn); font-weight: 700; }
.app { min-height: 100svh; display: grid; grid-template-columns: 280px 1fr; }
.side { position: sticky; top: 0; height: 100svh; padding: 28px; border-right: 1px solid var(--line); display: flex; flex-direction: column; justify-content: space-between; background: #f2f0e8; }
.side h1 { margin: 8px 0 10px; font-size: 42px; }
.side nav { display: grid; gap: 8px; margin-top: 36px; }
.side a { color: var(--ink); text-decoration: none; padding: 9px 0; }
.logout { color: var(--warn) !important; }
.workspace { padding: 30px; display: grid; gap: 22px; }
.topline { display: flex; align-items: center; justify-content: space-between; gap: 18px; border-bottom: 1px solid var(--line); padding-bottom: 20px; }
.topline h2 { margin: 0; font-size: clamp(28px, 5vw, 54px); letter-spacing: 0; }
.eyebrow { margin: 0; color: var(--accent); text-transform: uppercase; font-size: 12px; letter-spacing: .12em; font-weight: 800; }
.muted { color: var(--muted); line-height: 1.65; }
.pane { display: grid; gap: 18px; }
.pane.two { grid-template-columns: minmax(0, 1.3fr) minmax(280px, .7fr); }
.module { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 20px; min-width: 0; }
.module h3 { margin: 0 0 14px; font-size: 20px; }
.row { display: grid; grid-template-columns: 1fr auto; gap: 10px; align-items: start; }
.stack { display: grid; gap: 10px; }
.log { min-height: 260px; max-height: 430px; overflow: auto; display: grid; align-content: start; gap: 10px; padding: 12px; background: var(--soft); border-radius: 8px; margin-bottom: 12px; }
.msg { padding: 10px 12px; border-radius: 8px; background: white; border: 1px solid var(--line); }
.msg.assistant { border-left: 4px solid var(--accent); }
.msg.user { border-left: 4px solid #6c7890; }
.list { display: grid; gap: 10px; margin-top: 12px; }
.item { border: 1px solid var(--line); border-radius: 8px; padding: 12px; background: #fbfcfa; }
@media (max-width: 860px) {
  .app { grid-template-columns: 1fr; }
  .side { position: static; height: auto; }
  .pane.two, .row { grid-template-columns: 1fr; }
  .workspace { padding: 18px; }
}
"""


JS = """
const base = window.YOLOONG.base === "/" ? "" : window.YOLOONG.base;
const $ = (id) => document.getElementById(id);
async function api(path, options = {}) {
  const response = await fetch(base + path, {
    credentials: "same-origin",
    headers: {"Content-Type": "application/json", ...(options.headers || {})},
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || response.statusText);
  return data;
}
function showJson(el, data) { el.textContent = JSON.stringify(data, null, 2); }
function addMsg(role, text) {
  const node = document.createElement("div");
  node.className = `msg ${role}`;
  node.textContent = text;
  $("chatLog").appendChild(node);
  $("chatLog").scrollTop = $("chatLog").scrollHeight;
}
$("chatForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = $("chatInput").value.trim();
  if (!text) return;
  $("chatInput").value = "";
  addMsg("user", text);
  try {
    const data = await api("/api/chat", {method: "POST", body: JSON.stringify({text})});
    addMsg("assistant", data.text);
  } catch (error) {
    addMsg("assistant", "请求失败：" + error.message);
  }
});
$("tickButton").addEventListener("click", async () => {
  showJson($("tickOutput"), await api("/api/tick", {method: "POST", body: "{}"}));
});
$("proposePush").addEventListener("click", async () => {
  showJson($("approvalOutput"), await api("/api/propose", {method: "POST", body: JSON.stringify({name:"git push", description:"推送最新代码到 GitHub"})}));
});
$("loadApprovals").addEventListener("click", loadApprovals);
async function loadApprovals() {
  const data = await api("/api/approvals");
  $("approvalList").innerHTML = "";
  for (const item of data.approvals) {
    const node = document.createElement("div");
    node.className = "item";
    node.textContent = `${item.risk} · ${item.action} · ${item.reason} · ${item.request_id}`;
    $("approvalList").appendChild(node);
  }
  if (!data.approvals.length) $("approvalList").textContent = "暂无待审批。";
}
$("memoryForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = await api("/api/memory", {method:"POST", body: JSON.stringify({key:$("memoryKey").value, value:$("memoryValue").value})});
  $("memoryValue").value = "";
  $("memoryResults").textContent = data.ok ? "已保存。" : "保存失败。";
});
$("memorySearchForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = await api("/api/memory/search", {method:"POST", body: JSON.stringify({query:$("memoryQuery").value})});
  $("memoryResults").innerHTML = "";
  for (const [key, value] of data.results) {
    const node = document.createElement("div");
    node.className = "item";
    node.textContent = `${key}: ${value}`;
    $("memoryResults").appendChild(node);
  }
});
$("researchForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = await api("/api/research/queries", {method:"POST", body: JSON.stringify({topic:$("researchTopic").value})});
  $("researchResults").innerHTML = data.queries.map(q => `<div class="item">${q}</div>`).join("");
});
$("refreshStatus").addEventListener("click", refreshStatus);
async function refreshStatus() { showJson($("statusBox"), await api("/api/status")); }
refreshStatus();
"""
