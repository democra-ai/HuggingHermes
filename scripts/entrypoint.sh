#!/bin/sh
set -e

BOOT_START=$(date +%s)

echo "[entrypoint] HuggingHermes - Hermes Agent on HuggingFace Spaces"
echo "[entrypoint] =================================================="

# ── Hermes data directory ────────────────────────────────────────────────
mkdir -p /opt/data/cron /opt/data/sessions /opt/data/logs /opt/data/hooks \
         /opt/data/memories /opt/data/skills /opt/data/skins /opt/data/plans \
         /opt/data/workspace /opt/data/home

# ── Check Hermes installation ────────────────────────────────────────────
echo "[entrypoint] Checking Hermes Agent installation..."
if [ -d /app/hermes ]; then
  echo "  OK /app/hermes exists"
  ls /app/hermes/ 2>/dev/null | head -10
else
  echo "  ERROR: /app/hermes not found"
fi

# Check for hermes CLI
if command -v hermes >/dev/null 2>&1; then
  echo "  OK hermes CLI found: $(which hermes)"
elif [ -f /app/hermes/.venv/bin/hermes ]; then
  echo "  OK hermes CLI found in venv"
  export PATH="/app/hermes/.venv/bin:$PATH"
elif [ -f /app/hermes/hermes_cli/cli.py ]; then
  echo "  OK hermes_cli found, will use python -m"
fi

# Create logs directory
mkdir -p /home/hermes/logs
touch /home/hermes/logs/app.log

ENTRYPOINT_END=$(date +%s)
echo "[TIMER] Entrypoint (before sync_hf.py): $((ENTRYPOINT_END - BOOT_START))s"

# ── Start Hermes via sync_hf.py (handles persistence + process management)
echo "[entrypoint] Starting Hermes Agent via sync_hf.py..."
exec python3 -u /home/hermes/scripts/sync_hf.py
