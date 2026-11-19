# Uncensored Kaggle AI Agent & Local Web UI

An autonomous, uncensored code development agent powered by an abliterated LLM running on Kaggle's free GPU with persistent session memory, connected to a local Python Web UI.

## Architecture

1. **Remote Kaggle Backend (`remote-uncensored-ai.ipynb` / `setup_remote.py`):**
   - Runs Ollama on Kaggle (T4 x2 or P100 GPU).
   - Serves `huihui_ai/qwen2.5-coder-abliterate:7b` (Qwen 2.5 Coder 7B abliterated).
   - Exposes an OpenAI-compatible API (`/v1`) via Cloudflare Quick Tunnels (`cloudflared`).
   - Persists conversation memory across notebook restarts via Kaggle Dataset API (`sam-ai-memory`).
   - Push notification on boot via `ntfy.sh`.

2. **Local Autonomous Agent (`local_agent_webui.py` / `launch_agent.bat`):**
   - Zero-dependency local web interface running on `http://127.0.0.1:5050`.
   - Tool calling loop with full capabilities:
     - `read_file`: Inspect project files.
     - `write_file`: Create and overwrite code files.
     - `patch_file`: Exact search & replace surgical code patching.
     - `run_command`: Execute git and shell commands (`git clone`, `git commit`, tests, etc.) on the local PC.

## Quick Start

### 1. Push / Launch Kaggle Remote Session
```bash
python setup_remote.py
```
Wait for the `ntfy.sh` notification with the live Cloudflare tunnel URL.

### 2. Launch Local Agent Web UI
Double-click `launch_agent.bat` or run:
```bash
python local_agent_webui.py
```
Open [http://127.0.0.1:5050](http://127.0.0.1:5050) in your browser.
Enter the Cloudflare tunnel URL and your local repository path, then click **Save & Connect**.

