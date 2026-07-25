# LUIN — Executive Marketing Engine (v2)

**LUIN** is the spear of Lugh — the spear that never misses.

An automated, multi-agent marketing platform that orchestrates text, image, video, and audio generation end-to-end using autonomous AI agents, n8n workflows, local generative models (Flux.1, Wan2.2), and a centralized workspace CRM backend.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        LUIN Platform                        │
├──────────────┬──────────────┬──────────────┬───────────────┤
│  Frontend    │  Backend     │  Database    │  AI Services  │
│  (Netlify)   │  (Render)    │  (Supabase)  │  (Local)      │
│              │              │              │               │
│  • index.html│  • FastAPI   │  • PostgreSQL│  • ComfyUI    │
│  • dashboard │  • Auth      │  • RLS       │    (Flux.1)   │
│  • portal    │  • Campaigns │              │  • Wan2.2     │
│  • ultraplan │  • CRM       │              │  • Qwen3      │
│  • blog      │  • Generate  │              │  • n8n        │
│  • studio    │  • Brand     │              │               │
└──────────────┴──────────────┴──────────────┴───────────────┘
```

### Hosting
- **Frontend:** Netlify (static HTML/CSS/JS — no build step)
- **Backend:** Render (FastAPI + uvicorn)
- **Database:** Supabase PostgreSQL
- **AI Inference:** Local desktop (ComfyUI, LM Studio) + Groq for text

---

## Quick Start

### 1. Environment Setup

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 2. Backend (Local Development)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/api/docs

### 3. Frontend (Netlify)

The frontend is **pure static HTML/CSS/JS** — no build step required.

**Deploy to Netlify:**
1. Push this repo to GitHub
2. Connect repo in Netlify
3. Deploy — that's it

**Or run locally:**
```bash
# Use any static server
python -m http.server 3000 --directory frontend
# Open http://localhost:3000
```

### 4. Docker (Optional)

```bash
docker-compose up -d
# Backend: http://localhost:8000
# DB: localhost:5432
```

### 5. ComfyUI

```bash
scripts/launch-comfyui.bat
# Runs on localhost:8188
```

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/magic-link` | Request magic link |
| POST | `/api/v1/auth/token` | Exchange code for tokens |
| GET | `/api/v1/auth/me` | Get current user |
| POST | `/api/v1/auth/logout` | Logout |

### Workspaces
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/workspaces` | List all workspaces |
| GET | `/api/v1/workspaces/{id}/clients` | Get workspace details |
| GET | `/api/v1/workspaces/{id}/campaigns` | Get workspace campaigns |
| GET | `/api/v1/workspaces/{id}/crm-logs` | Get workspace CRM logs |

### Campaigns
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/campaigns` | List campaigns |
| POST | `/api/v1/campaigns` | Create campaign |
| POST | `/api/v1/campaigns/{id}/feedback` | Submit feedback |
| PUT | `/api/v1/campaigns/{id}/status` | Update status |
| GET | `/api/v1/campaigns/{id}` | Get campaign |
| GET | `/api/v1/campaigns/stats/{id}` | Get stats |

### AI Concierge
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/assistant/groq` | Stream chat (SSE) |
| POST | `/api/v1/assistant/groq/sync` | Sync chat |

### Generation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/generate` | Multi-modal generation |

### CRM
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/crm/event` | Tahuti webhook |
| POST | `/api/v1/crm/log` | Direct CRM log |
| GET | `/api/v1/crm/client/{id}` | Client profile |

### Brand Pack
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/brand/vectorize` | Raster to SVG |
| POST | `/api/v1/brand/palette` | Extract palette |
| POST | `/api/v1/brand/generate-pack` | Generate brand pack |

---

## Frontend Pages

| Page | File | Description |
|------|------|-------------|
| Landing | `frontend/index.html` | Public marketing site |
| Dashboard | `frontend/dashboard.html` | Admin dashboard (ARIA UI) |
| Client Portal | `frontend/portal.html` | Client-facing portal |
| Deep Research | `frontend/ultraplan.html` | Strategy brief generator |
| Blog | `frontend/blog.html` | Blog (placeholder) |
| Login | `frontend/login.html` | Magic-link auth |

---

## Key Features

- **Multi-Agent Orchestration:** JAMIE™ lead hunter, Writer copy engine, CREA™ image gen, Research signal harvesting
- **Multi-Modal Content:** Text, Flux.1 images, Wan2.2 video, audio generation
- **Workspace CRM:** Multi-tenant isolation with campaign tracking and brand assets
- **Ad-Hoc Studio:** Instant generation for any asset type
- **n8n Automation:** Webhook router, ComfyUI triggers, CRM sync, PostEverywhere dispatch
- **Enterprise Ready:** Stripe billing, corporate email validation, JWT auth, rate limiting

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Pure HTML/CSS/JS (Netlify) |
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 (Supabase) |
| Auth | Supabase Magic-Link + JWT |
| AI Text | Groq (llama-3.3-70b) |
| AI Image | ComfyUI (Flux.1 Dev) |
| AI Video | ComfyUI (Wan2.2) |
| AI Local | LM Studio (Qwen3) |
| Automation | n8n workflows |
| Deployment | Render + Netlify |

---

## Brand

**LUIN** — The spear of Lugh, the spear that never misses.

Brand colors: `#7c6fff` (accent), `#0a0a0f` (bg), `#111118` (surface)
Typography: Inter (Google Fonts)
Aesthetic: McKinsey dark-slate, high data density, razor-sharp typography

---

## Local Development

```bash
# 1. Start ComfyUI
scripts/launch-comfyui.bat

# 2. Start backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 3. Serve frontend
python -m http.server 3000 --directory frontend

# 4. Open http://localhost:3000
```

---

© 2026 LUIN. A spear that never misses.
