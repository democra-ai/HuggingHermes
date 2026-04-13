#!/bin/bash
set -e

BOOT_START=$(date +%s)

echo "[entrypoint] HermesFace — Hermes Agent on HuggingFace Spaces"
echo "[entrypoint] ===================================================="

HERMES_HOME="/opt/data"
INSTALL_DIR="/opt/hermes"

# ── Activate virtual environment ─────────────────────────────────────────
if [ -f "${INSTALL_DIR}/.venv/bin/activate" ]; then
  source "${INSTALL_DIR}/.venv/bin/activate"
  echo "[entrypoint] Activated venv: $(which python3)"
fi

# ── Ensure data directories ─────────────────────────────────────────────
mkdir -p "$HERMES_HOME"/{cron,sessions,logs,hooks,memories,skills,skins,plans,workspace,home}

# ── Bootstrap config files ───────────────────────────────────────────────
if [ ! -f "$HERMES_HOME/.env" ] && [ -f "$INSTALL_DIR/.env.example" ]; then
  cp "$INSTALL_DIR/.env.example" "$HERMES_HOME/.env"
  echo "[entrypoint] Created .env from example"
fi

if [ ! -f "$HERMES_HOME/config.yaml" ] && [ -f "$INSTALL_DIR/cli-config.yaml.example" ]; then
  cp "$INSTALL_DIR/cli-config.yaml.example" "$HERMES_HOME/config.yaml"
  echo "[entrypoint] Created config.yaml from example"
fi

if [ ! -f "$HERMES_HOME/SOUL.md" ] && [ -f "$INSTALL_DIR/docker/SOUL.md" ]; then
  cp "$INSTALL_DIR/docker/SOUL.md" "$HERMES_HOME/SOUL.md"
  echo "[entrypoint] Created SOUL.md from template"
fi

# ── Sync bundled skills ──────────────────────────────────────────────────
if [ -d "$INSTALL_DIR/skills" ] && [ -f "$INSTALL_DIR/tools/skills_sync.py" ]; then
  python3 "$INSTALL_DIR/tools/skills_sync.py" 2>&1 || echo "[entrypoint] Skills sync skipped"
fi

# ── Build artifacts check ───────────────────────────────────────────────
echo "[entrypoint] Build artifacts check:"
test -f "$INSTALL_DIR/run_agent.py" && echo "  OK run_agent.py" || echo "  INFO: run_agent.py not found"
test -f "$INSTALL_DIR/gateway/run.py" && echo "  OK gateway/run.py" || echo "  INFO: gateway/run.py not found"
test -d "$INSTALL_DIR/web" && echo "  OK web/ dashboard" || echo "  INFO: web/ not found"
command -v hermes >/dev/null 2>&1 && echo "  OK hermes CLI: $(which hermes)" || echo "  INFO: hermes CLI not in PATH"

# Create logs
mkdir -p /opt/data/logs
touch /opt/data/logs/app.log

ENTRYPOINT_END=$(date +%s)
echo "[TIMER] Entrypoint (before sync_hf.py): $((ENTRYPOINT_END - BOOT_START))s"

# ── Start Hermes via sync_hf.py (handles persistence + process management)
echo "[entrypoint] Starting Hermes Agent via sync_hf.py..."
exec python3 -u /opt/data/scripts/sync_hf.py
