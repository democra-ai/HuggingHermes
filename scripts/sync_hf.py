#!/usr/bin/env python3
"""
Hermes Agent HF Spaces Persistence — Full Directory Sync
=========================================================

Simplified persistence: upload/download the entire /opt/data directory
as-is to/from a Hugging Face Dataset repo.

- Startup:  snapshot_download  →  /opt/data
- Periodic: upload_folder      →  dataset hermes_data/
- Shutdown: final upload_folder →  dataset hermes_data/
"""

import os
import sys
import time
import threading
import subprocess
import signal
import json
import shutil
import tempfile
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime
# Set timeout BEFORE importing huggingface_hub
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "300")
os.environ.setdefault("HF_HUB_UPLOAD_TIMEOUT", "600")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("HF_HUB_VERBOSITY", "warning")

import logging as _logging
_logging.getLogger("huggingface_hub").setLevel(_logging.WARNING)
_logging.getLogger("huggingface_hub.utils").setLevel(_logging.WARNING)
_logging.getLogger("filelock").setLevel(_logging.WARNING)

from huggingface_hub import HfApi, snapshot_download

# ── Logging helper ──────────────────────────────────────────────────────────

class TeeLogger:
    """Duplicate output to stream and file."""
    def __init__(self, filename, stream):
        self.stream = stream
        self.file = open(filename, "a", encoding="utf-8")
    def write(self, message):
        self.stream.write(message)
        self.file.write(message)
        self.flush()
    def flush(self):
        self.stream.flush()
        self.file.flush()
    def fileno(self):
        return self.stream.fileno()

# ── Configuration ───────────────────────────────────────────────────────────

HF_TOKEN      = os.environ.get("HF_TOKEN")
HERMES_DATA   = Path("/opt/data")
APP_DIR       = Path("/opt/hermes")
DATASET_PATH  = "hermes_data"

AGENT_NAME = os.environ.get("AGENT_NAME", "HuggingHermes")

# HF Spaces built-in env vars (auto-set by HF runtime)
SPACE_HOST = os.environ.get("SPACE_HOST", "")
SPACE_ID   = os.environ.get("SPACE_ID", "")

SYNC_INTERVAL = int(os.environ.get("SYNC_INTERVAL", "60"))
AUTO_CREATE_DATASET = os.environ.get("AUTO_CREATE_DATASET", "true").lower() in ("true", "1", "yes")

# Dataset repo: auto-derive from SPACE_ID when not explicitly set.
# Format: {username}/{SpaceName}-data
HF_REPO_ID = os.environ.get("HERMES_DATASET_REPO", "")
if not HF_REPO_ID and SPACE_ID:
    HF_REPO_ID = f"{SPACE_ID}-data"
    print(f"[SYNC] HERMES_DATASET_REPO not set — auto-derived from SPACE_ID: {HF_REPO_ID}")
elif not HF_REPO_ID and HF_TOKEN:
    try:
        _api = HfApi(token=HF_TOKEN)
        _username = _api.whoami()["name"]
        HF_REPO_ID = f"{_username}/HuggingHermes-data"
        print(f"[SYNC] HERMES_DATASET_REPO not set — auto-derived from HF_TOKEN: {HF_REPO_ID}")
        del _api, _username
    except Exception as e:
        print(f"[SYNC] WARNING: Could not derive username from HF_TOKEN: {e}")
        HF_REPO_ID = ""

# Setup logging
log_dir = HERMES_DATA / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
sys.stdout = TeeLogger(log_dir / "sync.log", sys.stdout)
sys.stderr = sys.stdout


# ── Sync Manager ────────────────────────────────────────────────────────────

class HermesFullSync:
    """Upload/download the entire /opt/data directory to HF Dataset."""

    def __init__(self):
        self.enabled = False
        self.dataset_exists = False
        self.api = None

        if not HF_TOKEN:
            print("[SYNC] WARNING: HF_TOKEN not set. Persistence disabled.")
            return
        if not HF_REPO_ID:
            print("[SYNC] WARNING: Could not determine dataset repo (no SPACE_ID or HERMES_DATASET_REPO).")
            print("[SYNC] Persistence disabled.")
            return

        self.enabled = True
        self.api = HfApi(token=HF_TOKEN)
        self.dataset_exists = self._ensure_repo_exists()

    # ── Repo management ────────────────────────────────────────────────

    def _ensure_repo_exists(self):
        """Check if dataset repo exists; auto-create only when AUTO_CREATE_DATASET=true."""
        try:
            self.api.repo_info(repo_id=HF_REPO_ID, repo_type="dataset")
            print(f"[SYNC] Dataset repo found: {HF_REPO_ID}")
            return True
        except Exception:
            if not AUTO_CREATE_DATASET:
                print(f"[SYNC] Dataset repo NOT found: {HF_REPO_ID}")
                print(f"[SYNC]   Set AUTO_CREATE_DATASET=true to auto-create.")
                print(f"[SYNC] Persistence disabled (app will still run normally).")
                return False
            print(f"[SYNC] Dataset repo NOT found: {HF_REPO_ID} — creating...")
            try:
                self.api.create_repo(
                    repo_id=HF_REPO_ID,
                    repo_type="dataset",
                    private=True,
                )
                print(f"[SYNC] Dataset repo created: {HF_REPO_ID}")
                return True
            except Exception as e:
                print(f"[SYNC] Failed to create dataset repo: {e}")
                return False

    # ── Restore (startup) ─────────────────────────────────────────────

    def load_from_repo(self):
        """Download from dataset → /opt/data"""
        if not self.enabled:
            print("[SYNC] Persistence disabled - skipping restore")
            self._ensure_default_config()
            return

        if not self.dataset_exists:
            print(f"[SYNC] Dataset {HF_REPO_ID} does not exist - starting fresh")
            self._ensure_default_config()
            return

        print(f"[SYNC] Restoring /opt/data from dataset {HF_REPO_ID} ...")
        HERMES_DATA.mkdir(parents=True, exist_ok=True)

        try:
            files = self.api.list_repo_files(repo_id=HF_REPO_ID, repo_type="dataset")
            data_files = [f for f in files if f.startswith(f"{DATASET_PATH}/")]
            if not data_files:
                print(f"[SYNC] No {DATASET_PATH}/ folder in dataset. Starting fresh.")
                self._ensure_default_config()
                return

            print(f"[SYNC] Found {len(data_files)} files under {DATASET_PATH}/ in dataset")

            with tempfile.TemporaryDirectory() as tmpdir:
                snapshot_download(
                    repo_id=HF_REPO_ID,
                    repo_type="dataset",
                    allow_patterns=f"{DATASET_PATH}/**",
                    local_dir=tmpdir,
                    token=HF_TOKEN,
                )
                downloaded_root = Path(tmpdir) / DATASET_PATH
                if downloaded_root.exists():
                    for item in downloaded_root.rglob("*"):
                        if item.is_file():
                            rel = item.relative_to(downloaded_root)
                            dest = HERMES_DATA / rel
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(str(item), str(dest))
                    print("[SYNC] Restore completed.")
                else:
                    print("[SYNC] Downloaded snapshot but dir not found. Starting fresh.")

        except Exception as e:
            print(f"[SYNC] Restore failed: {e}")
            traceback.print_exc()

        self._ensure_default_config()
        self._debug_list_files()

    # ── Save (periodic + shutdown) ─────────────────────────────────────

    def save_to_repo(self):
        """Upload entire /opt/data directory → dataset (all files, no filtering)"""
        if not self.enabled:
            return
        if not HERMES_DATA.exists():
            print("[SYNC] /opt/data does not exist, nothing to save.")
            return

        if not self._ensure_repo_exists():
            print(f"[SYNC] Dataset {HF_REPO_ID} unavailable - skipping save")
            return

        print(f"[SYNC] Uploading /opt/data → dataset {HF_REPO_ID}/{DATASET_PATH}/ ...")

        try:
            total_size = 0
            file_count = 0
            for root, dirs, fls in os.walk(HERMES_DATA):
                for fn in fls:
                    fp = os.path.join(root, fn)
                    total_size += os.path.getsize(fp)
                    file_count += 1
            print(f"[SYNC] Uploading: {file_count} files, {total_size} bytes total")

            if file_count == 0:
                print("[SYNC] Nothing to upload.")
                return

            self.api.upload_folder(
                folder_path=str(HERMES_DATA),
                path_in_repo=DATASET_PATH,
                repo_id=HF_REPO_ID,
                repo_type="dataset",
                token=HF_TOKEN,
                commit_message=f"Sync hermes_data — {datetime.now().isoformat()}",
                ignore_patterns=[
                    "*.log",        # Log files — regenerated on boot
                    "*.lock",       # Lock files — stale after restart
                    "*.tmp",        # Temp files
                    "*.pid",        # PID files
                    "__pycache__",  # Python cache
                    "scripts/*",    # HuggingHermes scripts — from git, not data
                ],
            )
            print(f"[SYNC] Upload completed at {datetime.now().isoformat()}")

            try:
                files = self.api.list_repo_files(repo_id=HF_REPO_ID, repo_type="dataset")
                data_files = [f for f in files if f.startswith(f"{DATASET_PATH}/")]
                print(f"[SYNC] Dataset now has {len(data_files)} files under {DATASET_PATH}/")
            except Exception:
                pass

        except Exception as e:
            print(f"[SYNC] Upload failed: {e}")
            traceback.print_exc()

    # ── Config helpers ─────────────────────────────────────────────────

    def _ensure_default_config(self):
        """Ensure Hermes has config.yaml and .env for HF Spaces."""
        config_path = HERMES_DATA / "config.yaml"
        env_path = HERMES_DATA / ".env"
        soul_path = HERMES_DATA / "SOUL.md"

        # Bootstrap from Hermes templates if available
        if not config_path.exists():
            template = APP_DIR / "cli-config.yaml.example"
            if template.exists():
                shutil.copy2(str(template), str(config_path))
                print("[SYNC] Created config.yaml from Hermes template")
            else:
                # Minimal fallback config
                import yaml
                config = {
                    "agent": {"name": AGENT_NAME},
                    "server": {"host": "0.0.0.0", "port": 7860},
                }
                with open(config_path, "w") as f:
                    yaml.dump(config, f, default_flow_style=False)
                print(f"[SYNC] Created minimal config.yaml (agent={AGENT_NAME}, port=7860)")

        if not env_path.exists():
            template = APP_DIR / ".env.example"
            if template.exists():
                shutil.copy2(str(template), str(env_path))
                print("[SYNC] Created .env from Hermes template")
            else:
                env_lines = []
                for key in [
                    "OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
                    "NOUS_API_KEY", "GOOGLE_API_KEY", "MISTRAL_API_KEY",
                    "TELEGRAM_BOT_TOKEN", "DISCORD_BOT_TOKEN", "SLACK_BOT_TOKEN",
                ]:
                    val = os.environ.get(key, "")
                    if val:
                        env_lines.append(f"{key}={val}")
                if env_lines:
                    with open(env_path, "w") as f:
                        f.write("\n".join(env_lines) + "\n")
                    print(f"[SYNC] Created .env with {len(env_lines)} keys")

        if not soul_path.exists():
            template = APP_DIR / "docker" / "SOUL.md"
            if template.exists():
                shutil.copy2(str(template), str(soul_path))
                print("[SYNC] Created SOUL.md from Hermes template")
            else:
                with open(soul_path, "w") as f:
                    f.write(f"# {AGENT_NAME}\n\nI am {AGENT_NAME}, a self-improving AI assistant powered by Hermes Agent.\n")
                print("[SYNC] Created default SOUL.md")

    def _debug_list_files(self):
        try:
            count = sum(1 for _, _, files in os.walk(HERMES_DATA) for _ in files)
            print(f"[SYNC] Local /opt/data: {count} files")
        except Exception as e:
            print(f"[SYNC] listing failed: {e}")

    # ── Background sync loop ──────────────────────────────────────────

    def background_sync_loop(self, stop_event):
        print(f"[SYNC] Background sync started (interval={SYNC_INTERVAL}s)")
        while not stop_event.is_set():
            if stop_event.wait(timeout=SYNC_INTERVAL):
                break
            print(f"[SYNC] Periodic sync triggered at {datetime.now().isoformat()}")
            self.save_to_repo()

    # ── Health check HTTP server (port 7860) ─────────────────────────
    # HF Spaces requires an HTTP service on app_port to detect the app
    # is running. Hermes gateway is a messaging client (no HTTP server),
    # so we run a lightweight status page on 7860.

    def start_health_server(self):
        """Start a simple HTTP server on port 7860 for HF Spaces health check."""
        agent_name = AGENT_NAME
        hermes_process_ref = [None]  # mutable ref for the handler
        self._hermes_process_ref = hermes_process_ref

        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                proc = hermes_process_ref[0]
                running = proc is not None and proc.poll() is None
                status = "running" if running else "starting"
                body = json.dumps({
                    "status": status,
                    "agent": agent_name,
                    "framework": "hermes-agent",
                    "source": "https://github.com/NousResearch/hermes-agent",
                    "updated_at": datetime.now().isoformat(),
                })
                html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{agent_name}</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 640px; margin: 60px auto; padding: 20px; background: #0d1117; color: #c9d1d9; }}
h1 {{ color: #58a6ff; }} .status {{ padding: 12px; border-radius: 8px; background: #161b22; border: 1px solid #30363d; margin: 20px 0; }}
.dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; background: {"#3fb950" if running else "#d29922"}; }}
a {{ color: #58a6ff; }}
pre {{ background: #161b22; padding: 16px; border-radius: 8px; overflow-x: auto; border: 1px solid #30363d; }}
</style></head><body>
<h1>{agent_name}</h1>
<div class="status"><span class="dot"></span> Hermes Agent is <b>{status}</b></div>
<p>Self-improving AI assistant powered by <a href="https://github.com/NousResearch/hermes-agent">Hermes Agent</a> from Nous Research.</p>
<h3>API Status</h3>
<pre>{body}</pre>
<p><small>Deployed via <a href="https://github.com/democra-ai/HuggingHermes">HuggingHermes</a> on HuggingFace Spaces</small></p>
</body></html>"""
                if self.path == '/api/state' or self.path == '/status':
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(body.encode())
                else:
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(html.encode())

            def log_message(self, format, *args):
                pass  # Suppress access logs

        server = HTTPServer(('0.0.0.0', 7860), HealthHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print("[SYNC] Health check server started on port 7860")
        return server

    # ── Application runner ─────────────────────────────────────────────

    def run_hermes(self):
        """Start Hermes Agent process."""
        log_file = HERMES_DATA / "logs" / "startup.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        if not APP_DIR.exists():
            print(f"[SYNC] ERROR: App directory does not exist: {APP_DIR}")
            return None

        # Determine entry point — same order as Hermes docker/entrypoint.sh
        hermes_bin = shutil.which("hermes")
        venv_hermes = APP_DIR / ".venv" / "bin" / "hermes"
        gateway_run = APP_DIR / "gateway" / "run.py"
        run_agent = APP_DIR / "run_agent.py"

        if hermes_bin:
            entry_cmd = [hermes_bin, "gateway"]
        elif venv_hermes.exists():
            entry_cmd = [str(venv_hermes), "gateway"]
        elif gateway_run.exists():
            entry_cmd = [sys.executable, str(gateway_run)]
        elif run_agent.exists():
            entry_cmd = [sys.executable, str(run_agent)]
        else:
            print(f"[SYNC] ERROR: No Hermes entry point found in {APP_DIR}")
            try:
                print(f"[SYNC]   Contents: {list(APP_DIR.iterdir())[:20]}")
            except Exception:
                pass
            return None

        print(f"[SYNC] Launching: {' '.join(entry_cmd)}")
        print(f"[SYNC] Working directory: {APP_DIR}")
        print(f"[SYNC] Log file: {log_file}")

        log_fh = open(log_file, "a")

        # Pass entire environment to Hermes (all API keys are already in os.environ)
        env = os.environ.copy()
        env["HERMES_HOME"] = str(HERMES_DATA)

        # Enable API server on port 7860 for HF Spaces (OpenAI-compatible endpoint)
        # This provides /health, /v1/chat/completions, /v1/models, etc.
        env["API_SERVER_ENABLED"] = "true"
        env["API_SERVER_PORT"] = "7860"
        env["API_SERVER_HOST"] = "0.0.0.0"
        env["API_SERVER_CORS_ORIGINS"] = "https://huggingface.co,https://*.hf.space"
        print("[SYNC] API server configured on port 7860 (OpenAI-compatible)")

        try:
            process = subprocess.Popen(
                entry_cmd,
                cwd=str(APP_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
            )

            def copy_output():
                try:
                    for line in process.stdout:
                        log_fh.write(line)
                        log_fh.flush()
                        stripped = line.strip()
                        if not stripped:
                            continue
                        if any(skip in stripped for skip in [
                            'Downloading', 'Fetching', '%|', '━', '───',
                            'Already cached', 'Using cache', 'tokenizer',
                            '.safetensors', 'model-', 'shard',
                        ]):
                            continue
                        print(line, end='')
                except Exception as e:
                    print(f"[SYNC] Output copy error: {e}")
                finally:
                    log_fh.close()

            thread = threading.Thread(target=copy_output, daemon=True)
            thread.start()

            print(f"[SYNC] Process started with PID: {process.pid}")
            return process

        except Exception as e:
            log_fh.close()
            print(f"[SYNC] ERROR: Failed to start process: {e}")
            traceback.print_exc()
            return None


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    try:
        t_main_start = time.time()

        t0 = time.time()
        sync = HermesFullSync()
        print(f"[TIMER] sync_hf init: {time.time() - t0:.1f}s")

        # 1. Restore
        t0 = time.time()
        sync.load_from_repo()
        print(f"[TIMER] load_from_repo (restore): {time.time() - t0:.1f}s")

        # 2. Background sync
        stop_event = threading.Event()
        t = threading.Thread(target=sync.background_sync_loop, args=(stop_event,), daemon=True)
        t.start()

        # 3. Start health check HTTP server (port 7860 — required by HF Spaces)
        # Serves a status page while Hermes gateway boots up.
        health_server = sync.start_health_server()

        # 4. Start application
        # Shutdown health server before Hermes starts (API server will take port 7860)
        print("[SYNC] Stopping health server (API server will take port 7860)...")
        health_server.shutdown()
        time.sleep(1)

        t0 = time.time()
        process = sync.run_hermes()
        if process and hasattr(sync, '_hermes_process_ref'):
            sync._hermes_process_ref[0] = process
        print(f"[TIMER] run_hermes launch: {time.time() - t0:.1f}s")
        print(f"[TIMER] Total startup (init → app launched): {time.time() - t_main_start:.1f}s")

        # Signal handler
        def handle_signal(sig, frame):
            print(f"\n[SYNC] Signal {sig} received. Shutting down...")
            stop_event.set()
            t.join(timeout=10)
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            print("[SYNC] Final sync...")
            sync.save_to_repo()
            sys.exit(0)

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        # Wait
        if process is None:
            print("[SYNC] ERROR: Failed to start Hermes process. Exiting.")
            stop_event.set()
            t.join(timeout=5)
            sys.exit(1)

        exit_code = process.wait()
        print(f"[SYNC] Hermes exited with code {exit_code}")
        stop_event.set()
        t.join(timeout=10)
        print("[SYNC] Final sync...")
        sync.save_to_repo()
        sys.exit(exit_code)

    except Exception as e:
        print(f"[SYNC] FATAL ERROR in main: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
