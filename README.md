---
title: HuggingHermes
emoji: 🔱
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
license: mit
short_description: Deploy Hermes Agent on HuggingFace Spaces for free
app_port: 7860
tags:
  - huggingface
  - hermes-agent
  - nousresearch
  - agents
  - ai-assistant
  - chatbot
  - deployment
  - docker
  - llm
  - one-click-deploy
  - persistent-storage
  - telegram
  - whatsapp
---

<div align="center">

# 🔱 HuggingHermes

### Deploy [Hermes Agent](https://github.com/NousResearch/hermes-agent) on HuggingFace Spaces — free, persistent, always online.

**No server? No problem.** Get a fully-featured, self-improving AI assistant running 24/7
on HuggingFace's free tier — 2 vCPU, 16 GB RAM, 50 GB storage, zero cost.

[![Hermes Agent](https://img.shields.io/badge/Hermes_Agent-v0.9.0-blueviolet?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyTDIgN2wxMCA1IDEwLTV6TTIgMTdsIDEwIDUgMTAtNSIvPjwvc3ZnPg==)](https://github.com/NousResearch/hermes-agent)
[![HuggingFace Space](https://img.shields.io/badge/%F0%9F%A4%97%20HuggingFace-Space-yellow)](https://huggingface.co/spaces/tao-shen/HuggingHermes)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-SDK-blue?logo=docker)](Dockerfile)

</div>

---

## What is HuggingHermes?

HuggingHermes wraps [Hermes Agent](https://github.com/NousResearch/hermes-agent) — Nous Research's open-source, self-improving AI assistant — with everything needed to run on HuggingFace Spaces:

- **HF Dataset Persistence** — Config, skills, memories, and conversations auto-sync to a private HF Dataset repo so nothing is lost on restart
- **OpenAI-compatible API** — Built-in `/v1/chat/completions` endpoint on port 7860; connect Open WebUI, LobeChat, ChatBox, or any OpenAI-compatible frontend
- **16+ Messaging Platforms** — Telegram, Discord, Slack, WhatsApp, Signal, WeChat, iMessage, and more — all from one Space
- **Self-improving Skills** — Hermes creates and refines skills from experience during use
- **Persistent Memory** — LLM-powered memory system with search and summarization across sessions
- **47 Built-in Tools** — Terminal, file ops, web search, vision, image generation, browser automation
- **Multi-model Support** — OpenRouter (200+ models), OpenAI, Anthropic, Nous Portal, Google, Mistral

## Quick Start

### One-click deploy

1. **Duplicate this Space** → Click "Duplicate this Space" on the [HuggingFace Space page](https://huggingface.co/spaces/tao-shen/HuggingHermes)
2. **Set secrets** → In your Space Settings → Repository Secrets:
   - `HF_TOKEN` — HuggingFace token with write access ([create one](https://huggingface.co/settings/tokens))
   - At least one LLM provider key (e.g. `OPENROUTER_API_KEY`, `OPENAI_API_KEY`)
3. **Done** — Your Hermes Agent is live in ~5 minutes

### Local Docker

```bash
git clone https://github.com/democra-ai/HuggingHermes.git
cd HuggingHermes
cp .env.example .env    # Edit with your API keys
docker build -t hugginghermes .
docker run -p 7860:7860 --env-file .env hugginghermes
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│  HuggingFace Space (Docker, cpu-basic)          │
│                                                 │
│  ┌──────────────┐    ┌───────────────────────┐  │
│  │ sync_hf.py   │───▶│  Hermes Agent         │  │
│  │  (persistence│    │  ├─ Gateway (messaging)│  │
│  │   manager)   │    │  ├─ API Server (:7860) │  │
│  └──────┬───────┘    │  ├─ Skills Engine      │  │
│         │            │  ├─ Memory System       │  │
│         │            │  └─ 47 Tools           │  │
│         ▼            └───────────────────────┘  │
│  ┌──────────────┐                               │
│  │ HF Dataset   │  ◀── Auto-sync every 60s     │
│  │ (private)    │      Config, skills, memories │
│  └──────────────┘                               │
└─────────────────────────────────────────────────┘
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HF_TOKEN` | Yes | — | HuggingFace token (write access) |
| `OPENROUTER_API_KEY` | Recommended | — | OpenRouter API key (200+ models) |
| `OPENAI_API_KEY` | Optional | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | Optional | — | Anthropic API key |
| `NOUS_API_KEY` | Optional | — | Nous Portal API key |
| `TELEGRAM_BOT_TOKEN` | Optional | — | Telegram bot token |
| `DISCORD_BOT_TOKEN` | Optional | — | Discord bot token |
| `SLACK_BOT_TOKEN` | Optional | — | Slack bot token |
| `HERMES_DATASET_REPO` | Optional | Auto-derived | Dataset repo for persistence |
| `AUTO_CREATE_DATASET` | Optional | `true` | Auto-create dataset repo |
| `SYNC_INTERVAL` | Optional | `60` | Backup interval in seconds |
| `AGENT_NAME` | Optional | `HuggingHermes` | Agent display name |
| `TZ` | Optional | `UTC` | Timezone |

All [Hermes Agent environment variables](https://github.com/NousResearch/hermes-agent) are passed through directly.

## API Endpoints

The Space exposes an OpenAI-compatible API on port 7860:

```bash
# Health check
curl https://your-space.hf.space/health

# List models
curl https://your-space.hf.space/v1/models

# Chat completion
curl https://your-space.hf.space/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "hermes-agent", "messages": [{"role": "user", "content": "Hello!"}]}'
```

## How It Works

1. **Build** — Clones Hermes Agent from source, installs Python (uv) + Node.js + Playwright dependencies
2. **Restore** — Downloads persisted data from HF Dataset → `/opt/data`
3. **Start** — Launches Hermes gateway with API server on port 7860
4. **Sync** — Background thread uploads `/opt/data` → HF Dataset every 60 seconds
5. **Shutdown** — Final sync on SIGTERM to prevent data loss

## Connecting Messaging Platforms

Set the appropriate bot token as a Space Secret, then configure via Hermes:

| Platform | Secret | Docs |
|----------|--------|------|
| Telegram | `TELEGRAM_BOT_TOKEN` | [BotFather](https://t.me/botfather) |
| Discord | `DISCORD_BOT_TOKEN` | [Discord Developer Portal](https://discord.com/developers/applications) |
| Slack | `SLACK_BOT_TOKEN` | [Slack API](https://api.slack.com/apps) |
| WhatsApp | QR code pairing | Automatic via gateway |
| Signal | Via linked device | Configure in gateway |

## Credits

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) by [Nous Research](https://nousresearch.com/) — the self-improving AI assistant framework
- [HuggingFace Spaces](https://huggingface.co/spaces) — free Docker hosting for ML apps
- Deployment pattern inspired by [HuggingClaw](https://github.com/democra-ai/HuggingClaw)

## License

MIT — see [LICENSE](LICENSE).
