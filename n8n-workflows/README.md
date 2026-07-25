# LUIN n8n Workflow Templates

Production-ready n8n workflow JSON files for the LUIN platform's multi-modal content pipeline.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    LUIN n8n Workflow Stack                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ 01-Webhook   │    │ 05-Image     │    │ 06-Video     │  │
│  │   Router     │    │ Generation   │    │ Generation   │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                    │          │
│  ┌──────▼───────┐    ┌──────▼───────┐    ┌──────▼───────┐  │
│  │ 03-Tahuti    │    │ 07-Long-Form │    │ 08-Audio/    │  │
│  │   CRM Log    │    │ Video Orch.  │    │ Voiceover    │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                    │          │
│  ┌──────▼───────────────────▼────────────────────▼───────┐  │
│  │              09-CRM & Backend Sync Pipeline            │  │
│  └───────────────────────────┬───────────────────────────┘  │
│                              │                               │
│                    ┌─────────▼─────────┐                    │
│                    │  Luin FastAPI     │                    │
│                    │  :8000            │                    │
│                    │  /api/v1/generate │                    │
│                    └───────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## Workflows

### Text Generation Pipeline
| File | Name | Trigger | Purpose |
|------|------|---------|---------|
| `01-webhook-router.json` | Webhook Router | Webhook | Central routing by event_type |
| `02-comfyui-generation.json` | ComfyUI Generation | Webhook | Direct image/video generation trigger |
| `03-tahuti-crm-log.json` | Tahuti CRM Log | Webhook | CRM message logging |
| `04-posteverywhere-dispatch.json` | PostEverywhere Dispatch | Webhook | Social media publishing |

### Multi-Modal Asset Generation
| File | Name | Trigger | Purpose |
|------|------|---------|---------|
| `05-image-generation.json` | Image Generation Pipeline | Daily 8am | Flux.1 Dev image generation with QA review loop |
| `06-video-generation.json` | Video Generation Pipeline | Daily 10am | Wan2.2 T2V video generation with storyboard QA |
| `07-longform-video-orchestration.json` | Long-Form Video Orchestrator | Daily 12pm | Master prompt → scene segmentation → batch generation → assembly |
| `08-audio-voiceover.json` | Audio/Voiceover Pipeline | Daily 2pm | F5-TTS voiceover generation with QA review |

### Backend Synchronization
| File | Name | Trigger | Purpose |
|------|------|---------|---------|
| `09-crm-backend-sync.json` | CRM & Backend Sync | Every 30min | Workspace metrics sync, attention alerts, campaign stats |

## Pipeline Structure (Following Reference Pattern)

Each multi-modal workflow follows the exact structural pattern from the reference text workflow:

```
1. Trigger (Schedule/Webhook)
   ↓
2. Data Ingestion (Fetch workspaces, campaigns, brand tokens)
   ↓
3. Analysis (LLM generates brief/prompt/storyboard)
   ↓
4. Creative Generation (ComfyUI/Flux/Wan2.2/F5-TTS)
   ↓
5. QA Verification (LLM reviews output for brand compliance)
   ↓
6. Conditional Routing (IF approved → publish; IF rejected → regenerate)
   ↓
7. Retry Loop (Prepare rewrite → regenerate → re-QA → final verdict)
   ↓
8. Publish/Sync (PostEverywhere or backend API)
   ↓
9. Logging (History log for deduplication)
```

## Webhook Endpoints

| Endpoint | Workflow | Method | Purpose |
|----------|----------|--------|---------|
| `/webhook/luin` | 01-webhook-router | POST | Central webhook router |
| `/comfyui-gen` | 02-comfyui-generation | POST | Direct ComfyUI trigger |
| `/tahuti-crm` | 03-tahuti-crm-log | POST | CRM log ingestion |
| `/posteverywhere` | 04-posteverywhere-dispatch | POST | Social media dispatch |

## Scheduled Triggers

| Workflow | Cron Expression | Time (UTC) |
|----------|-----------------|------------|
| 05-image-generation | `0 8 * * *` | 8:00 AM daily |
| 06-video-generation | `0 10 * * *` | 10:00 AM daily |
| 07-longform-video-orchestration | `0 12 * * *` | 12:00 PM daily |
| 08-audio-voiceover | `0 14 * * *` | 2:00 PM daily |
| 09-crm-backend-sync | `*/30 * * * *` | Every 30 minutes |

## Importing Workflows

### Automated (Recommended)
```bash
cd n8n-workflows
bash import-workflows.sh
# or with custom URL:
bash import-workflows.sh http://localhost:5678
```

### Manual
1. Open n8n at `http://localhost:5678`
2. Click ⋯ → Import from File
3. Select the `.json` file
4. Toggle the workflow ON

## Configuration

### Required Environment Variables (n8n Settings)
| Variable | Value | Purpose |
|----------|-------|---------|
| `LUIN_BACKEND_URL` | `http://host.docker.internal:8000` | Luin FastAPI |
| `COMFYUI_URL` | `http://host.docker.internal:8188` | ComfyUI endpoint |
| `TAHUTI_BASE_URL` | `http://host.docker.internal:18789` | Tahuti gateway |
| `POSTEVERYWHERE_API_KEY` | `[your-key]` | Social media API |

### HTTP Authentication Credentials
Create in n8n Settings → Credentials → Add New:
- **Header Auth** for Luin Backend (API key auth)
- **Header Auth** for Tahuti Gateway (API key auth)
- **Header Auth** for PostEverywhere (API key auth)

## Long-Form Video Pipeline Details

The long-form video orchestration (`07-longform-video-orchestration.json`) implements:

1. **Master Prompt Segmentation** — LLM breaks master prompt into scene descriptions
2. **Scene Loop** — Each scene generated independently via ComfyUI
3. **Async Status Polling** — Waits for each scene to complete
4. **Progress Tracking** — Accumulates completed scenes
5. **Assembly** — Merges all scenes into final video with voiceover
6. **QA Review** — Reviews assembled video for coherence
7. **Backend Sync** — Pushes final video to Luin FastAPI

## Image/Video/Audio Pipeline Details

Each multi-modal pipeline (`05`, `06`, `08`) implements:

1. **Workspace Context** — Fetches workspace brand tokens/palette
2. **Brief Generation** — LLM generates creative brief/storyboard
3. **ComfyUI Submission** — Sends prompt to ComfyUI endpoint
4. **Async Polling** — Waits for generation to complete
5. **QA Review** — LLM reviews output for brand compliance
6. **Conditional Routing** — Approves or triggers regeneration
7. **Backend Sync** — Pushes final asset to Luin FastAPI

## CRM Sync Pipeline Details

The CRM sync pipeline (`09-crm-backend-sync.json`) implements:

1. **Workspace Iteration** — Loops through all workspaces
2. **Campaign Stats** — Fetches pending/approved/published counts
3. **CRM Log Count** — Fetches latest CRM activity
4. **Metrics Compilation** — Aggregates workspace health
5. **Attention Detection** — Flags workspaces needing review
6. **Backend Sync** — Pushes metrics to Luin FastAPI
7. **Alert Logging** — Creates CRM log for attention items

## Testing

### Test Image Generation
```bash
curl -X POST http://localhost:5678/webhook/comfyui-gen \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A professional headshot with natural lighting",
    "model": "flux1-dev",
    "workspace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }'
```

### Test Video Generation
```bash
curl -X POST http://localhost:5678/webhook/comfyui-gen \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A cinematic brand story with product showcase",
    "model": "wan2.2_ti2v_5B_fp16",
    "duration": 30,
    "workspace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }'
```

### Test Audio Generation
```bash
curl -X POST http://localhost:5678/webhook/tahuti-crm \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "audio_generation",
    "workspace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "text": "Welcome to our brand story..."
  }'
```

## Troubleshooting

### ComfyUI Connection Issues
- Verify ComfyUI is running: `scripts/launch-comfyui.bat`
- Check endpoint: `curl http://localhost:8188/prompt`
- Ensure GPU VRAM is available for Wan2.2 model

### Backend Sync Failures
- Verify Luin backend is running: `curl http://localhost:8000/health`
- Check workspace IDs match database
- Verify API keys in n8n credentials

### QA Review Failures
- Check LLM endpoint is reachable
- Verify model names match your setup
- Check prompt formatting in Code nodes

## Next Steps

1. Import all workflows: `bash import-workflows.sh`
2. Enable each workflow (toggle switch)
3. Configure credentials in n8n Settings
4. Test with curl or n8n's test mode
5. Monitor logs for errors
6. Adjust cron schedules as needed

---

**Last Updated:** 2026-07-23  
**Total Workflows:** 9 (4 text + 5 multi-modal)  
**Architecture:** Multi-agent pipeline with QA verification loops
