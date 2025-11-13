# Profiler API

Psychological profiling service using LLM analysis

## 🌐 Production Environment

**URL**: `https://api.hey-watch.me/profiler/`

### Current Status

**✅ Production Ready** (2025-11-13)

| Item | Value |
|------|-------|
| **LLM Provider** | Groq |
| **Model** | openai/gpt-oss-120b (reasoning model) |
| **Reasoning Effort** | medium |
| **Deploy Date** | 2025-11-13 |
| **Status** | healthy ✅ |

**Health Check**:
```bash
curl https://api.hey-watch.me/profiler/health | jq
```

**Expected Response**:
```json
{
  "status": "healthy",
  "llm_provider": "groq",
  "llm_model": "openai/gpt-oss-120b"
}
```

### Infrastructure

- Microservice architecture
- SSL/HTTPS enabled, CORS configured
- Docker + ECR + systemd
- CI/CD auto-deploy (GitHub Actions)

---

## 🎯 Overview

This API provides psychological profiling by analyzing aggregated audio data using LLM (ChatGPT/Groq).

### Main Features

- **Spot Profiler**: Single recording analysis (`/spot-profiler`)
- **Daily Profiler**: Daily cumulative analysis (`/daily-profiler`) 🚧 Coming soon
- **Weekly Profiler**: Weekly trend analysis (`/weekly-profiler`) 🚧 Coming soon
- **Monthly Profiler**: Monthly long-term analysis (`/monthly-profiler`) 🚧 Coming soon
- **Multiple LLM Provider Support**: Easy switching between OpenAI, Groq, etc.
- **Retry Functionality**: Ensures API call stability

---

## 🗺️ Routing Details

| Item | Value | Description |
|------|-------|-------------|
| **🏷️ Service Name** | Profiler API | LLM psychological profiling |
| **📦 Function** | LLM Gateway | ChatGPT/Groq analysis execution |
| | | |
| **🌐 External Access (Nginx)** | | |
| └ Public Endpoint | `https://api.hey-watch.me/profiler/` | ✅ Unified naming convention |
| └ Nginx Config File | `/etc/nginx/sites-available/api.hey-watch.me` | |
| └ proxy_pass Target | `http://localhost:8051/` | Internal forwarding |
| └ Timeout | 180 seconds | read/connect/send |
| | | |
| **🔌 API Internal Endpoints** | | |
| └ Health Check | `/health` | GET |
| └ **Spot Profiler** | `/spot-profiler` | POST - Called by Lambda |
| └ **Daily Profiler** | `/daily-profiler` | POST - Daily summary (🚧 Coming soon) |
| └ **Weekly Profiler** | `/weekly-profiler` | POST - Weekly analysis (🚧 Coming soon) |
| └ **Monthly Profiler** | `/monthly-profiler` | POST - Monthly analysis (🚧 Coming soon) |
| | | |
| **🐳 Docker/Container** | | |
| └ Container Name | `profiler-api` | ✅ Unified naming |
| └ Port (Internal) | 8051 | Inside container |
| └ Port (Public) | `127.0.0.1:8051:8051` | localhost only |
| └ Health Check | `/health` | Docker healthcheck |
| | | |
| **☁️ AWS ECR** | | |
| └ Repository Name | `watchme-profiler` | ✅ ECR repository |
| └ Region | ap-southeast-2 (Sydney) | |
| └ URI | `754724220380.dkr.ecr.ap-southeast-2.amazonaws.com/watchme-profiler:latest` | |
| | | |
| **⚙️ systemd** | | |
| └ Service Name | `profiler-api.service` | docker-compose management |
| └ Startup Command | `docker-compose up -d` | |
| └ Auto Start | enabled | Auto-start on server reboot |
| | | |
| **📂 Directory** | | |
| └ Source Code | `/Users/kaya.matsumoto/projects/watchme/api/profiler` | Local |
| └ GitHub Repository | `hey-watchme/api-profiler` | |
| └ EC2 Location | `/home/ubuntu/profiler-api` | Production execution directory |
| | | |
| **🔗 Caller** | | |
| └ Lambda Function (Spot) | `watchme-audio-worker` | |
| └ Call URL (Spot) | ✅ `https://api.hey-watch.me/profiler/spot-profiler` | |
| └ Environment Variable | `API_BASE_URL=https://api.hey-watch.me` | Inside Lambda |

---

## 🤖 LLM Provider Settings

### Design Concept

This API **supports multiple LLM providers** and can be easily switched.

**Purpose**:
- Quick migration to new models
- Cost optimization (different providers have different pricing)
- Immediate rollback on performance issues
- Multiple models prepared in advance (API keys configured, can switch anytime)

**Features**:
- ✅ No client-side changes required (app/other APIs)
- ✅ 1-line code change → git push to switch
- ✅ Can keep 3-5 providers on standby
- ✅ Model version upgrades follow same procedure

### Currently In Use

- Provider: **Groq**
- Model: **openai/gpt-oss-120b** (reasoning model)
- Reasoning Effort: **medium**

### Supported Providers

| Provider | Example Models | Environment Variable | Status |
|----------|---------------|---------------------|--------|
| **OpenAI** | gpt-4o, gpt-4o-mini, gpt-5-nano, o1-preview | OPENAI_API_KEY | ✅ Configured |
| **Groq** | llama-3.3-70b-versatile, llama-3.1-8b-instant | GROQ_API_KEY | ✅ Configured |
| **Groq via OpenAI** | openai/gpt-oss-120b (reasoning model) | GROQ_API_KEY | ✅ Configured (currently in use) |

### How to Switch Providers

See `llm_providers.py` - change `CURRENT_PROVIDER` and `CURRENT_MODEL` constants.

---

## 📌 API Endpoints

### Active Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/health` | GET | Health check |
| `/spot-profiler` | POST | Spot profiler analysis (single recording) |
| `/daily-profiler` | POST | Daily profiler analysis (1 day) 🚧 Coming soon |
| `/weekly-profiler` | POST | Weekly profiler analysis (7 days) 🚧 Coming soon |
| `/monthly-profiler` | POST | Monthly profiler analysis (30 days) 🚧 Coming soon |

---

## 🔌 Endpoint Details

### 1. Health Check

```bash
curl https://api.hey-watch.me/profiler/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-13T00:00:00.000000",
  "llm_provider": "groq",
  "llm_model": "openai/gpt-oss-120b"
}
```

### 2. Spot Profiler

**v1.0.0 Specification**:
- ✅ `recorded_at` parameter (UTC timestamp)
- ✅ Microservice architecture compliant

```bash
curl -X POST https://api.hey-watch.me/profiler/spot-profiler \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "9f7d6e27-98c3-4c19-bdfb-f7fda58b9a93",
    "recorded_at": "2025-11-13T12:31:01+00:00"
  }'
```

**Processing Flow**:
1. Fetch prompt from `spot_aggregators.prompt`
2. Execute LLM (Groq/ChatGPT) analysis
3. Save result to `spot_results` table

**Response:**
```json
{
  "status": "success",
  "message": "Spot profiler analysis completed (DB save successful)",
  "device_id": "9f7d6e27-98c3-4c19-bdfb-f7fda58b9a93",
  "recorded_at": "2025-11-13T12:31:01+00:00",
  "analysis_result": {
    "summary": "Description of the situation",
    "vibe_score": -30,
    "behavior": "Working"
  },
  "database_save": true,
  "processed_at": "2025-11-13T12:35:00.000Z",
  "model_used": "groq/openai/gpt-oss-120b"
}
```

---

## 📊 Database Structure

### spot_aggregators Table (Input Source)

**Prompt fetch source**

This API reads prompts from `spot_aggregators.prompt`.

```sql
CREATE TABLE spot_aggregators (
  device_id TEXT NOT NULL,
  recorded_at TIMESTAMPTZ NOT NULL,  -- UTC
  prompt TEXT NOT NULL,
  context_data JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (device_id, recorded_at)
);
```

### spot_results Table (Output Destination)

**Spot profiler analysis results**

```sql
CREATE TABLE spot_results (
  device_id TEXT NOT NULL,
  recorded_at TIMESTAMPTZ NOT NULL,  -- UTC
  vibe_score DOUBLE PRECISION NULL,
  profile_result JSONB NOT NULL,     -- Full analysis result
  created_at TIMESTAMPTZ DEFAULT NOW(),
  llm_model TEXT NULL,
  PRIMARY KEY (device_id, recorded_at)
);
```

**Saved Fields:**
- `vibe_score`: Psychological score (-100 to +100)
- `profile_result`: Complete analysis result (JSONB)
  - `summary`: Situation summary
  - `psychological_analysis`: Mood state, description, emotion changes
  - `behavioral_analysis`: Detected activities, behavior pattern, situation context
  - `acoustic_metrics`: Speech ratio, loudness, voice stability, pitch variability
  - `key_observations`: Notable findings
- `llm_model`: Model used (e.g., "groq/openai/gpt-oss-120b")
- `created_at`: Auto-generated timestamp

---

## 🚀 Deployment

### CI/CD Auto-Deploy

```bash
# Commit & push triggers auto-deploy
git add .
git commit -m "feat: Add new feature"
git push origin main

# GitHub Actions auto-executes (approx. 5 minutes)
# https://github.com/hey-watchme/api-profiler/actions
```

**Auto-execution content:**
1. Build ARM64-compatible Docker image
2. Push to ECR
3. Auto-deploy on EC2
4. Health check

### Service Management Commands (EC2)

```bash
# Check service status
sudo systemctl status profiler-api

# Restart service
sudo systemctl restart profiler-api

# View logs
sudo journalctl -u profiler-api -f
docker logs profiler-api --tail 50
```

---

## 🔧 Environment Variables (.env)

```bash
# LLM API Keys
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk-...  # Only when using Groq

# Supabase Settings
SUPABASE_URL=https://qvtlwotzuzbavrzqhyvt.supabase.co
SUPABASE_KEY=your-supabase-key
```

**Note**: Model specification is done in `llm_providers.py` (not environment variables).

---

## 📦 Dependencies

```txt
fastapi==0.100.0
uvicorn==0.23.0
pydantic==2.0.2
python-dotenv==1.0.0
openai>=1.0.0
groq>=0.4.0
requests>=2.31.0
python-multipart>=0.0.6
aiohttp>=3.8.0
tenacity>=8.2.0
httpx==0.24.1
gotrue==1.3.0
supabase==2.3.4
```

---

## 🔗 Related Services

- **Aggregator API**: `api/aggregator`
- **iOS App**: `ios_watchme_v9`

---

## 📚 API Documentation

- **Swagger UI**: https://api.hey-watch.me/profiler/docs
- **ReDoc**: https://api.hey-watch.me/profiler/redoc

---

## 📝 Changelog

### v1.0.0 (2025-11-13)

**Initial Release - Production Deployment Completed** ✅

**Architecture:**
- New Profiler API created (separated from Scorer API)
- Microservice architecture compliant
- UTC-unified time management with `recorded_at`
- CI/CD auto-deploy pipeline (GitHub Actions → ECR → EC2)

**API Changes:**
- Input: `spot_aggregators.prompt` (reads from Supabase)
- Output: `spot_results` (writes to Supabase)
- Request parameter: `recorded_at` (UTC timestamp)
- Endpoint: `/spot-profiler`

**Database Schema:**
- Table: `spot_results`
- Columns: `device_id`, `recorded_at`, `vibe_score`, `profile_result` (JSONB), `llm_model`, `created_at`
- Removed deprecated columns: `local_date`, `local_time`, `behavior_score`, `emotion_score`, `composite_score`
- RLS disabled (internal API only)

**Infrastructure:**
- Container: `profiler-api` (port 8051)
- ECR: `watchme-profiler`
- systemd: `profiler-api.service`
- Nginx: `/profiler/` → `http://localhost:8051/`
- Health check: `/health`

**Testing:**
- Production test completed successfully
- Database save verified
- LLM model: Groq OpenAI GPT-OSS-120B

---

**Developer**: WatchMe
**Version**: 1.0.0
**Status**: ✅ Production Ready
