# HuggingHermes — Hermes Agent on Hugging Face Spaces
# Uses official pre-built image to avoid lengthy builds on cpu-basic

# ── Stage 1: Pull pre-built Hermes Agent ─────────────────────────────────
FROM ghcr.io/nousresearch/hermes-agent:latest AS hermes-prebuilt

# ── Stage 2: Runtime ─────────────────────────────────────────────────────
FROM python:3.11-bookworm
SHELL ["/bin/bash", "-c"]

# ── System dependencies (root) ───────────────────────────────────────────
RUN echo "[build] Installing system deps..." && START=$(date +%s) \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
     git ca-certificates curl nodejs npm \
  && rm -rf /var/lib/apt/lists/* \
  && pip3 install --no-cache-dir huggingface_hub requests pyyaml \
  && useradd -m -s /bin/bash hermes \
  && mkdir -p /opt/data /app/hermes \
  && chown -R hermes:hermes /opt/data /app/hermes \
  && echo "[build] System deps: $(($(date +%s) - START))s"

# ── Copy pre-built Hermes Agent ──────────────────────────────────────────
COPY --from=hermes-prebuilt --chown=hermes:hermes /app /app/hermes

USER hermes
ENV HOME=/home/hermes
WORKDIR /app

# ── Prepare runtime dirs ────────────────────────────────────────────────
RUN mkdir -p /opt/data/cron \
             /opt/data/sessions \
             /opt/data/logs \
             /opt/data/hooks \
             /opt/data/memories \
             /opt/data/skills \
             /opt/data/skins \
             /opt/data/plans \
             /opt/data/workspace \
             /opt/data/home

# ── Scripts ──────────────────────────────────────────────────────────────
ARG CACHE_BUST=2026-04-13-v1
RUN echo "Build: ${CACHE_BUST}"
COPY --chown=hermes:hermes scripts /home/hermes/scripts
RUN chmod +x /home/hermes/scripts/entrypoint.sh

ENV PYTHONUNBUFFERED=1
ENV PATH="/home/hermes/.local/bin:/app/hermes/.venv/bin:$PATH"
WORKDIR /home/hermes

CMD ["/home/hermes/scripts/entrypoint.sh"]
