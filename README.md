---
title: HermesFace
emoji: 🔱
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
license: mit
short_description: Free always-on AI assistant, no hardware required
app_port: 7860
tags:
  - huggingface
  - hermes-agent
  - nousresearch
  - chatbot
  - llm
  - ai-assistant
  - whatsapp
  - telegram
  - text-generation
  - openai-api
  - openai-compatible
  - huggingface-spaces
  - docker
  - deployment
  - persistent-storage
  - agents
  - multi-channel
  - free-tier
  - one-click-deploy
  - self-hosted
  - messaging-bot
  - self-improving
---

<div align="center">

# 🔱 HermesFace

### Your always-on, self-improving AI assistant — free, no server needed

**No Mac Mini? No problem.** Get a fully-featured AI assistant running 24/7
on HuggingFace's free tier — 2 vCPU, 16 GB RAM, 50 GB storage, zero cost.

<sub>Telegram · Discord · Slack · WhatsApp · Signal · WeChat · 16+ channels · Self-improving skills · Persistent memory</sub>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Hugging Face](https://img.shields.io/badge/🤗-HF%20Space-yellow)](https://huggingface.co/spaces/tao-shen/HermesFace)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?logo=github)](https://github.com/democra-ai/HermesFace)
[![Hermes Agent](https://img.shields.io/badge/Hermes_Agent-v0.9.0-blueviolet)](https://github.com/NousResearch/hermes-agent)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)
[![OpenAI Compatible](https://img.shields.io/badge/OpenAI--compatible-API-green)](https://github.com/NousResearch/hermes-agent)
[![Telegram](https://img.shields.io/badge/Telegram-Enabled-26A5E4?logo=telegram)](https://telegram.org/)
[![Discord](https://img.shields.io/badge/Discord-Enabled-5865F2?logo=discord)](https://discord.com/)
[![Free Tier](https://img.shields.io/badge/Free%20Tier-16GB%20RAM-brightgreen)](https://huggingface.co/spaces)

</div>

---

## What you get

In about 5 minutes, you'll have a **free, always-on, self-improving AI assistant** connected to Telegram, Discord, Slack, WhatsApp, and 16+ other channels — no server, no subscription, no hardware required.

| | |
|---|---|
| **Free forever** | HuggingFace Spaces gives you 2 vCPU + 16 GB RAM at no cost |
| **Always online** | Your conversations, skills, memories, and config survive every restart |
| **16+ channels** | Telegram, Discord, Slack, WhatsApp, Signal, WeChat, iMessage, and more |
| **Self-improving** | Hermes creates and refines skills from experience during use |
| **Persistent memory** | LLM-powered memory with search and summarization across sessions |
| **47 built-in tools** | Terminal, file ops, web search, vision, image generation, browser automation |
| **Any LLM** | OpenRouter (200+ models, free tier available), OpenAI, Claude, Gemini, Nous Portal |
| **Web dashboard** | React-based UI for managing config, API keys, and monitoring sessions |
| **One-click deploy** | Duplicate the Space, set two secrets, done |

> **Powered by [Hermes Agent](https://github.com/NousResearch/hermes-agent)** — Nous Research's open-source, self-improving AI assistant that normally requires your own machine. HermesFace makes it run for free on HuggingFace Spaces by adding data persistence via HF Dataset sync.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  HuggingFace Space (Docker, cpu-basic)              │
│                                                     │
│  ┌──────────────┐    ┌────────────────────────────┐ │
│  │ sync_hf.py   │───▶│  Hermes Agent              │ │
│  │ (persistence │    │  ├─ Web Dashboard (:7860)   │ │
│  │  manager)    │    │  ├─ Gateway (messaging)     │ │
│  │              │    │  ├─ Skills Engine            │ │
│  └──────┬───────┘    │  ├─ Memory System           │ │
│         │            │  ├─ Cron Scheduler           │ │
│         ▼            │  └─ 47 Tools                 │ │
│  ┌──────────────┐    └────────────────────────────┘ │
│  │ HF Dataset   │  ◀── Auto-sync every 60s         │
│  │ (private)    │      Config, skills, memories     │
│  └──────────────┘                                   │
└─────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Duplicate this Space

Click **Duplicate this Space** on the [HermesFace Space page](https://huggingface.co/spaces/tao-shen/HermesFace).

### 2. Set Secrets

Go to **Settings → Repository secrets** and add the following. The only two you *must* set are `HF_TOKEN` and one API key.

| Secret | Status | Description | Example |
|--------|:------:|-------------|---------|
| `HF_TOKEN` | **Required** | HF Access Token with write permission ([create one](https://huggingface.co/settings/tokens)) | `hf_AbCdEfGhIjKlMnOpQrStUvWxYz` |
| `AUTO_CREATE_DATASET` | **Recommended** | Set to `true` — HermesFace will automatically create a private backup dataset on first startup. No manual setup needed. | `true` |
| `OPENROUTER_API_KEY` | Recommended | [OpenRouter](https://openrouter.ai) API key — 200+ models, free tier available. Easiest way to get started. | `sk-or-v1-xxxxxxxxxxxx` |
| `OPENAI_API_KEY` | Optional | OpenAI API key | `sk-proj-xxxxxxxxxxxx` |
| `ANTHROPIC_API_KEY` | Optional | Anthropic Claude API key | `sk-ant-xxxxxxxxxxxx` |
| `NOUS_API_KEY` | Optional | Nous Portal API key | `nous-xxxxxxxxxxxx` |
| `GOOGLE_API_KEY` | Optional | Google / Gemini API key | `AIzaSyXxXxXxXxXx` |

### Data Persistence

HermesFace syncs `/opt/data` (conversations, skills, memories, config) to a private HuggingFace Dataset repo so your data survives every restart.

**Option A — Auto mode (recommended)**

1. Set `AUTO_CREATE_DATASET` = `true` in your Space secrets
2. Set `HF_TOKEN` with write permission
3. Done — on first startup, HermesFace automatically creates a private Dataset repo named `your-username/SpaceName-data`. Each duplicated Space gets its own isolated dataset.

**Option B — Manual mode**

1. Go to [huggingface.co/new-dataset](https://huggingface.co/new-dataset) and create a **private** Dataset repo (e.g. `your-name/HermesFace-data`)
2. Set `HERMES_DATASET_REPO` = `your-name/HermesFace-data` in your Space secrets
3. Set `HF_TOKEN` with write permission
4. Done — HermesFace will sync to this repo every 60 seconds

### Environment Variables

Fine-tune persistence and performance. Set these as **Repository Secrets** in HF Spaces, or in `.env` for local Docker.

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTO_CREATE_DATASET` | `true` | Auto-create the Dataset repo on first startup |
| `SYNC_INTERVAL` | `60` | Backup interval in seconds |
| `AGENT_NAME` | `HermesFace` | Agent display name in messaging platforms |
| `TZ` | `UTC` | Timezone for logs and scheduled tasks |

> For the full list (including all Hermes Agent variables), see [`.env.example`](.env.example).

### 3. Open the Dashboard

Visit your Space URL. The Hermes Agent web dashboard provides:
- **Status Page** — agent status and session activity
- **Config Page** — dynamic configuration editor
- **Env Page** — API key management

Messaging integrations (Telegram, Discord, WhatsApp) can be configured through the dashboard or via environment variables.

## Configuration

HermesFace supports **all Hermes Agent environment variables** — it passes the entire environment to the Hermes process (`env=os.environ.copy()`), so any variable from the [Hermes Agent docs](https://github.com/NousResearch/hermes-agent) works out of the box in HF Spaces. This includes:

- **API Keys** — `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `NOUS_API_KEY`, `GOOGLE_API_KEY`, `MISTRAL_API_KEY`
- **Messaging** — `TELEGRAM_BOT_TOKEN`, `DISCORD_BOT_TOKEN`, `SLACK_BOT_TOKEN`
- **Terminal** — `TERMINAL_BACKEND`, `TERMINAL_TIMEOUT`
- **Browser** — `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID`

HermesFace adds its own variables for persistence and deployment: `HF_TOKEN`, `HERMES_DATASET_REPO`, `AUTO_CREATE_DATASET`, `SYNC_INTERVAL`, etc. See [`.env.example`](.env.example) for the complete reference.

## Connecting Messaging Platforms

Set the appropriate bot token as a Space Secret:

| Platform | Secret | Docs |
|----------|--------|------|
| Telegram | `TELEGRAM_BOT_TOKEN` | [BotFather](https://t.me/botfather) |
| Discord | `DISCORD_BOT_TOKEN` | [Discord Developer Portal](https://discord.com/developers/applications) |
| Slack | `SLACK_BOT_TOKEN` | [Slack API](https://api.slack.com/apps) |
| WhatsApp | QR code pairing | Automatic via gateway |
| Signal | Via linked device | Configure in gateway |
| WeChat | `WEIXIN_APP_ID` + `WEIXIN_APP_SECRET` | WeChat Open Platform |

## Local Docker

```bash
git clone https://github.com/democra-ai/HermesFace.git
cd HermesFace
cp .env.example .env    # Edit with your API keys
docker build -t hermesface .
docker run -p 7860:7860 --env-file .env hermesface
```

## Acknowledgments

- **[Hermes Agent](https://github.com/NousResearch/hermes-agent)** by [Nous Research](https://nousresearch.com/) — the self-improving AI assistant framework
- **[HuggingFace Spaces](https://huggingface.co/spaces)** — free Docker hosting for ML apps

## License

MIT
