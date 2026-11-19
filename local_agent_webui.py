import http.server
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

PORT = 5050
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "backend_url": "https://ashley-chair-collecting-extended.trycloudflare.com",
        "repo_path": os.getcwd(),
        "model_name": "huihui_ai/qwen2.5-coder-abliterate:7b"
    }

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Uncensored Code Agent</title>
<style>
:root {
  --bg: #0d1117;
  --surface: #161b22;
  --surface-border: #30363d;
  --primary: #58a6ff;
  --primary-hover: #1f6feb;
  --accent: #238636;
  --accent-hover: #2ea043;
  --text: #c9d1d9;
  --text-dim: #8b949e;
  --danger: #da3633;
  --code-bg: #090d13;
}
* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; }
body { background: var(--bg); color: var(--text); display: flex; height: 100vh; overflow: hidden; }

/* Sidebar */
#sidebar {
  width: 320px;
  background: var(--surface);
  border-right: 1px solid var(--surface-border);
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--surface-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.sidebar-header h2 { font-size: 15px; color: #fff; display: flex; align-items: center; gap: 8px; }
.status-pill {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 12px;
  background: #21262d;
  color: var(--text-dim);
  display: flex;
  align-items: center;
  gap: 6px;
}
.status-pill.online { background: rgba(35, 134, 54, 0.2); color: #3fb950; }
.status-pill .dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }

.config-box {
  padding: 12px 16px;
  border-bottom: 1px solid var(--surface-border);
  background: #11151c;
  font-size: 12px;
}
.config-row { margin-bottom: 8px; }
.config-row label { display: block; color: var(--text-dim); margin-bottom: 4px; font-weight: 600; font-size: 11px; }
.config-row input {
  width: 100%;
  background: var(--bg);
  border: 1px solid var(--surface-border);
  color: #fff;
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.config-row input:focus { outline: none; border-color: var(--primary); }
.btn-small {
  background: var(--primary);
  color: #fff;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
}
.btn-small:hover { background: var(--primary-hover); }

/* File tree */
.file-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.file-item {
  padding: 5px 8px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-dim);
}
.file-item:hover { background: #21262d; color: #fff; }
.file-item.active { background: #1f6feb33; color: var(--primary); font-weight: 600; }
.file-item.dir { font-weight: 600; color: #fff; }

/* Main Chat & Editor area */
#main {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.message {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}
.message.user {
  align-self: flex-end;
  background: #1f6feb;
  color: #fff;
  border-bottom-right-radius: 2px;
}
.message.assistant {
  align-self: flex-start;
  background: var(--surface);
  border: 1px solid var(--surface-border);
  color: var(--text);
  border-bottom-left-radius: 2px;
}

/* Tool execution card */
.tool-card {
  align-self: flex-start;
  width: 90%;
  background: #090d13;
  border: 1px solid #30363d;
  border-left: 3px solid #58a6ff;
  border-radius: 6px;
  padding: 10px 14px;
  font-size: 12px;
  margin: 4px 0;
}
.tool-title { font-weight: bold; color: var(--primary); margin-bottom: 6px; display: flex; align-items: center; gap: 6px; }
.tool-content {
  background: #040608;
  padding: 8px;
  border-radius: 4px;
  font-family: monospace;
  max-height: 180px;
  overflow-y: auto;
  color: #8b949e;
}
.diff-added { color: #3fb950; }
.diff-removed { color: #f85149; }

/* Input bar */
.input-area {
  padding: 16px 20px;
  background: var(--surface);
  border-top: 1px solid var(--surface-border);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.quick-tools {
  display: flex;
  gap: 8px;
  align-items: center;
}
.quick-btn {
  background: #21262d;
  color: var(--text);
  border: 1px solid var(--surface-border);
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
}
.quick-btn:hover { background: #30363d; color: #fff; }
.input-row { display: flex; gap: 10px; }
#user-input {
  flex: 1;
  background: var(--bg);
  border: 1px solid var(--surface-border);
  color: #fff;
  padding: 12px 14px;
  border-radius: 6px;
  font-size: 14px;
  resize: none;
  min-height: 48px;
  max-height: 120px;
}
#user-input:focus { outline: none; border-color: var(--primary); }
#send-btn {
  background: var(--accent);
  color: #fff;
  border: none;
  padding: 0 20px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}
#send-btn:hover { background: var(--accent-hover); }
#send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
</head>
<body>

<div id="sidebar">
  <div class="sidebar-header">
    <h2>⚡ Repo Agent</h2>
    <div id="status-badge" class="status-pill"><span class="dot"></span> <span id="status-text">Checking</span></div>
  </div>

  <div class="config-box">
    <div class="config-row">
      <label>KAGGLE API TUNNEL URL</label>
      <input type="text" id="backend-input" placeholder="https://xxxx.trycloudflare.com">
    </div>
    <div class="config-row">
      <label>LOCAL REPOSITORY PATH</label>
      <input type="text" id="repo-input" placeholder="C:\\path\\to\\your\\repo">
    </div>
    <div style="display:flex; gap:8px;">
      <button class="btn-small" onclick="saveConfiguration()">Save & Connect</button>
      <button class="btn-small" style="background:#30363d;" onclick="resetState()">Reset UI</button>
    </div>
  </div>

  <div class="sidebar-header" style="background:#13171e; padding:10px 16px;">
    <span style="font-size:12px; font-weight:600; color:var(--text-dim);">FILES IN REPO</span>
    <button class="quick-btn" style="padding:2px 6px;" onclick="loadFiles()">Refresh</button>
  </div>
  <div class="file-list" id="file-tree">
    <div style="padding:10px; font-size:12px; color:var(--text-dim);">Loading files...</div>
  </div>
</div>

<div id="main">
  <div class="chat-container" id="chat-box">
    <div class="message assistant">
      👋 <strong>Uncensored Code Agent Ready.</strong><br>
      I have direct access to your local machine and repository. I can clone GitHub repos, read code, write files, apply patches, and run git commands.<br><br>
      Tell me what repository you want to clone or what you'd like me to build or modify!
    </div>
  </div>

  <div class="input-area">
    <div class="quick-tools">
      <span style="font-size:11px; color:var(--text-dim); margin-right:4px;">Quick Commands:</span>
      <button class="quick-btn" onclick="sendQuickPrompt('Check git status and explain current changes')">Git Status</button>
      <button class="quick-btn" onclick="sendQuickPrompt('Review repo structure and suggest improvements')">Repo Review</button>
      <button class="quick-btn" onclick="sendQuickPrompt('Commit all pending changes with a descriptive message')">Git Commit</button>
    </div>
    <div class="input-row">
      <textarea id="user-input" placeholder="Ask the agent to edit files, clone repos, add features, or run git commands..." onkeydown="handleKeyDown(event)" oninput="handleInput()"></textarea>
      <button id="send-btn" onclick="sendMessage()">Send</button>
    </div>
  </div>
</div>

<script>
let currentConfig = {};
let isProcessing = false;
let conversationHistory = [];

function handleInput() {
  const sendBtn = document.getElementById('send-btn');
  if (!isProcessing) {
    sendBtn.disabled = false;
    sendBtn.innerText = 'Send';
  }
}

async function init() {
  const res = await fetch('/api/config');
  currentConfig = await res.json();
  document.getElementById('backend-input').value = currentConfig.backend_url || '';
  document.getElementById('repo-input').value = currentConfig.repo_path || '';
  checkConnection();
  loadFiles();
}

function resetState() {
  isProcessing = false;
  document.getElementById('send-btn').disabled = false;
  document.getElementById('send-btn').innerText = 'Send';
  checkConnection();
}

async function saveConfiguration() {
  const backend = document.getElementById('backend-input').value.trim();
  const repo = document.getElementById('repo-input').value.trim();
  const res = await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ backend_url: backend, repo_path: repo })
  });
  currentConfig = await res.json();
  checkConnection();
  loadFiles();
}

async function checkConnection() {
  const badge = document.getElementById('status-badge');
  const text = document.getElementById('status-text');
  try {
    const res = await fetch('/api/check_connection');
    const data = await res.json();
    if (data.online) {
      badge.className = 'status-pill online';
      text.innerText = 'Online (' + (data.model || 'Connected') + ')';
    } else {
      badge.className = 'status-pill';
      text.innerText = 'Offline';
    }
  } catch (e) {
    badge.className = 'status-pill';
    text.innerText = 'Error';
  }
}

async function loadFiles() {
  const tree = document.getElementById('file-tree');
  try {
    const res = await fetch('/api/files');
    const files = await res.json();
    if (files.error) {
      tree.innerHTML = `<div style="padding:10px; color:#da3633; font-size:12px;">${files.error}</div>`;
      return;
    }
    tree.innerHTML = '';
    files.forEach(f => {
      const el = document.createElement('div');
      el.className = 'file-item' + (f.is_dir ? ' dir' : '');
      el.innerHTML = (f.is_dir ? '📁 ' : '📄 ') + f.name;
      if (!f.is_dir) {
        el.onclick = () => previewFile(f.path);
      }
      tree.appendChild(el);
    });
  } catch(e) {
    tree.innerHTML = `<div style="padding:10px; color:#da3633; font-size:12px;">Failed to load files</div>`;
  }
}

async function previewFile(path) {
  const res = await fetch('/api/read_file?path=' + encodeURIComponent(path));
  const data = await res.json();
  if (data.content) {
    appendCard("📄 File: " + path, data.content);
  }
}

function handleKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function sendQuickPrompt(prompt) {
  document.getElementById('user-input').value = prompt;
  sendMessage();
}

function appendMessage(role, text) {
  const box = document.getElementById('chat-box');
  const msg = document.createElement('div');
  msg.className = 'message ' + role;
  msg.innerText = text;
  box.appendChild(msg);
  box.scrollTop = box.scrollHeight;
  return msg;
}

function appendCard(title, content) {
  const box = document.getElementById('chat-box');
  const card = document.createElement('div');
  card.className = 'tool-card';
  card.innerHTML = `<div class="tool-title">${title}</div><div class="tool-content">${escapeHtml(content)}</div>`;
  box.appendChild(card);
  box.scrollTop = box.scrollHeight;
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

async function sendMessage() {
  if (isProcessing) return;
  const input = document.getElementById('user-input');
  const text = input.value.trim();
  if (!text) return;

  appendMessage('user', text);
  conversationHistory.push({ role: 'user', content: text });
  input.value = '';
  isProcessing = true;
  const sendBtn = document.getElementById('send-btn');
  sendBtn.disabled = true;
  sendBtn.innerText = 'Working...';

  const assistantMsg = appendMessage('assistant', 'Thinking and inspecting repository...');

  const safetyTimeout = setTimeout(() => {
    if (isProcessing) {
      console.warn("Watchdog timeout: resetting button");
      isProcessing = false;
      sendBtn.disabled = false;
      sendBtn.innerText = 'Send';
    }
  }, 90000);

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: text, history: conversationHistory.slice(-10) })
    });

    if (!res.ok) {
      throw new Error('Server returned HTTP ' + res.status);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    assistantMsg.innerText = '';
    let streamFinished = false;
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\\n');
      buffer = lines.pop(); // Retain incomplete line fragment
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith('data: ')) continue;
        const dataStr = trimmed.substring(6).trim();
        if (dataStr === '[DONE]') {
          streamFinished = true;
          break;
        }
        try {
          const event = JSON.parse(dataStr);
          if (event.type === 'tool') {
            appendCard(event.title, event.content);
          } else if (event.type === 'token') {
            assistantMsg.innerText += event.content;
            document.getElementById('chat-box').scrollTop = document.getElementById('chat-box').scrollHeight;
          } else if (event.type === 'error') {
            appendCard("⚠️ Error", event.content);
          }
        } catch(e) {}
      }
      if (streamFinished) {
        try { await reader.cancel(); } catch(e) {}
        break;
      }
    }
    if (assistantMsg.innerText) {
      conversationHistory.push({ role: 'assistant', content: assistantMsg.innerText });
    }
  } catch(e) {
    if (!assistantMsg.innerText) {
      assistantMsg.innerText = '⚠️ Error communicating with agent: ' + e;
    }
  } finally {
    clearTimeout(safetyTimeout);
    isProcessing = false;
    sendBtn.disabled = false;
    sendBtn.innerText = 'Send';
    document.getElementById('user-input').focus();
    loadFiles();
  }
}

window.onload = init;
</script>
</body>
</html>
"""

class AgentServer(http.server.BaseHTTPRequestHandler):
    config = load_config()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif parsed.path == "/api/config":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(self.config).encode("utf-8"))
        elif parsed.path == "/api/check_connection":
            online, model = self.check_backend()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"online": online, "model": model}).encode("utf-8"))
        elif parsed.path == "/api/files":
            files = self.list_repo_files()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(files).encode("utf-8"))
        elif parsed.path == "/api/read_file":
            qs = urllib.parse.parse_qs(parsed.query)
            p = qs.get("path", [""])[0]
            content = self.read_local_file(p)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"content": content}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")

        if parsed.path == "/api/config":
            try:
                data = json.loads(body)
                if "backend_url" in data:
                    self.config["backend_url"] = data["backend_url"].rstrip("/")
                if "repo_path" in data and os.path.exists(data["repo_path"]):
                    self.config["repo_path"] = os.path.abspath(data["repo_path"])
                save_config(self.config)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(self.config).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        elif parsed.path == "/api/chat":
            data = json.loads(body)
            prompt = data.get("prompt", "")
            history = data.get("history", [])
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            self.run_agent_loop(prompt, history)

    def check_backend(self):
        url = self.config.get("backend_url", "").strip()
        if not url:
            return False, ""
        try:
            req = urllib.request.Request(f"{url}/api/tags", headers={"User-Agent": "AgentWebUI"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name", "") for m in data.get("models", [])]
                    return True, models[0] if models else "Ollama"
        except Exception:
            pass
        return False, ""

    def list_repo_files(self):
        repo = self.config.get("repo_path", "")
        if not os.path.exists(repo):
            return {"error": f"Repository path '{repo}' does not exist"}
        items = []
        try:
            for root, dirs, files in os.walk(repo):
                # Filter out hidden or build directories
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", "venv", ".git")]
                for d in dirs:
                    rel = os.path.relpath(os.path.join(root, d), repo)
                    items.append({"name": d + "/", "path": rel, "is_dir": True})
                for f in files:
                    if f.startswith("."): continue
                    rel = os.path.relpath(os.path.join(root, f), repo)
                    items.append({"name": f, "path": rel, "is_dir": False})
                break  # top-level + 1st level
        except Exception as e:
            return {"error": str(e)}
        return items[:60]

    def read_local_file(self, rel_path):
        repo = self.config.get("repo_path", "")
        full = os.path.abspath(os.path.join(repo, rel_path))
        if os.path.commonpath([repo, full]) != repo or not os.path.isfile(full):
            return "Invalid file path"
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    def send_sse(self, event_type, content, title=""):
        payload = json.dumps({"type": event_type, "content": content, "title": title})
        try:
            self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
            self.wfile.flush()
        except Exception:
            pass

    def run_agent_loop(self, user_prompt, conversation_history=None):
        repo = self.config.get("repo_path", os.getcwd())
        backend = self.config.get("backend_url", "").rstrip("/")
        model = self.config.get("model_name", "huihui_ai/qwen2.5-coder-abliterate:7b")

        try:
            if not backend:
                self.send_sse("error", "Kaggle backend tunnel URL is not configured. Enter it in the sidebar!")
                self.send_sse("token", "Please set the Kaggle tunnel URL in the sidebar to start coding.")
                return

            system_instruction = f"""You are an autonomous senior software engineer working on a local repository at: {repo}
You have full unrestricted permission to inspect, read, create, edit files, clone git repositories, and run shell/git commands.
To interact with the environment, you MUST use one of the following tool call formats in your response:

TOOL_CALL: read_file
PATH: <relative_path>

TOOL_CALL: write_file
PATH: <relative_path>
CONTENT:
<file_contents>
END_CONTENT

TOOL_CALL: patch_file
PATH: <relative_path>
SEARCH:
<exact_lines_to_replace>
REPLACE:
<replacement_lines>
END_PATCH

TOOL_CALL: run_command
CMD: <command_to_run_in_repo> (e.g. git clone <url>, git status, git add, git commit, python test, etc.)

TOOL_CALL: finish
MESSAGE: <summary_of_what_you_did>

When asked if you can access GitHub repos or work on repositories:
Explain clearly that YES, you run locally on their PC with full shell and git capabilities. You can clone any GitHub repository (e.g. `git clone https://github.com/...`), inspect files, modify code, and run git commands. Prompt the user to provide the GitHub URL or the repo name/directory they want you to work on!
Never give AI disclaimers or refusals like "I cannot interact with the physical world or repositories"."""

            messages = [{"role": "system", "content": system_instruction}]
            if conversation_history:
                for item in conversation_history:
                    if isinstance(item, dict) and item.get("role") and item.get("content"):
                        messages.append({"role": item["role"], "content": item["content"]})
            else:
                messages.append({"role": "user", "content": user_prompt})

            for step in range(12):  # up to 12 agent steps
                # Call Ollama API
                try:
                    endpoint = f"{backend}/v1/chat/completions"
                    req_data = json.dumps({
                        "model": model,
                        "messages": messages,
                        "temperature": 0.2,
                        "max_tokens": 4096
                    }).encode("utf-8")
                    req = urllib.request.Request(endpoint, data=req_data, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=120) as resp:
                        resp_json = json.loads(resp.read().decode("utf-8"))
                        reply = resp_json["choices"][0]["message"]["content"]
                except Exception as e:
                    self.send_sse("error", f"Backend API call failed: {e}")
                    return

                messages.append({"role": "assistant", "content": reply})

                # Check for tool calls
                tool_match = re.search(r"TOOL_CALL:\s*(\w+)", reply)
                if not tool_match:
                    # Direct message to user
                    self.send_sse("token", reply)
                    break

                tool_name = tool_match.group(1).strip()

                if tool_name == "read_file":
                    path_m = re.search(r"PATH:\s*(.+)", reply)
                    rel_path = path_m.group(1).strip() if path_m else ""
                    self.send_sse("tool", f"Reading {rel_path}...", title=f"🔍 Reading: {rel_path}")
                    content = self.read_local_file(rel_path)
                    tool_output = f"FILE CONTENT ({rel_path}):\n{content}"
                    messages.append({"role": "user", "content": f"OBSERVATION:\n{tool_output}"})

                elif tool_name == "write_file":
                    path_m = re.search(r"PATH:\s*(.+)", reply)
                    rel_path = path_m.group(1).strip() if path_m else ""
                    content_m = re.search(r"CONTENT:\n([\s\S]*?)(?:\nEND_CONTENT|$)", reply)
                    new_content = content_m.group(1) if content_m else ""
                    full_path = os.path.abspath(os.path.join(repo, rel_path))
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w", encoding="utf-8", errors="replace") as f:
                        f.write(new_content)
                    self.send_sse("tool", f"Saved {len(new_content)} characters to {rel_path}", title=f"✏️ Wrote: {rel_path}")
                    messages.append({"role": "user", "content": f"OBSERVATION: File {rel_path} successfully written."})

                elif tool_name == "patch_file":
                    path_m = re.search(r"PATH:\s*(.+)", reply)
                    rel_path = path_m.group(1).strip() if path_m else ""
                    search_m = re.search(r"SEARCH:\n([\s\S]*?)\nREPLACE:\n([\s\S]*?)(?:\nEND_PATCH|$)", reply)
                    if search_m:
                        search_block = search_m.group(1)
                        replace_block = search_m.group(2)
                        full_path = os.path.abspath(os.path.join(repo, rel_path))
                        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                            old = f.read()
                        if search_block in old:
                            new = old.replace(search_block, replace_block, 1)
                            with open(full_path, "w", encoding="utf-8", errors="replace") as f:
                                f.write(new)
                            self.send_sse("tool", f"Patched {rel_path}", title=f"🩹 Patched: {rel_path}")
                            messages.append({"role": "user", "content": f"OBSERVATION: File {rel_path} successfully patched."})
                        else:
                            messages.append({"role": "user", "content": f"ERROR: SEARCH block not found in {rel_path}."})
                    else:
                        messages.append({"role": "user", "content": "ERROR: Malformed patch format."})

                elif tool_name == "run_command":
                    cmd_m = re.search(r"CMD:\s*(.+)", reply)
                    cmd = cmd_m.group(1).strip() if cmd_m else ""
                    self.send_sse("tool", f"Executing: {cmd}", title=f"⚙️ Command: {cmd}")
                    try:
                        proc = subprocess.run(cmd, cwd=repo, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
                        out = (proc.stdout + "\n" + proc.stderr).strip()
                        self.send_sse("tool", out or "(Command succeeded with no output)", title=f"⚙️ Output: {cmd}")
                        messages.append({"role": "user", "content": f"COMMAND OUTPUT:\n{out}"})
                    except Exception as ex:
                        self.send_sse("error", f"Command failed: {ex}")
                        messages.append({"role": "user", "content": f"COMMAND ERROR: {ex}"})

                elif tool_name == "finish":
                    msg_m = re.search(r"MESSAGE:\s*([\s\S]*)", reply)
                    fin_msg = msg_m.group(1).strip() if msg_m else reply
                    self.send_sse("token", fin_msg)
                    break

        except Exception as top_err:
            self.send_sse("error", f"Agent execution error: {top_err}")
        finally:
            try:
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
            except Exception:
                pass

def run():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), AgentServer)
    print("=" * 60)
    print(f"🚀 Uncensored Local Agent Web UI running on http://127.0.0.1:{PORT}")
    print("=" * 60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")

if __name__ == "__main__":
    run()
