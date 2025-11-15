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

- **Spot Profiler**: Single recording analysis (`/spot-profiler`) ✅ Production
- **Daily Profiler**: Daily cumulative analysis (`/daily-profiler`) ✅ Production (2025-11-15)
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
| └ **Spot Profiler** | `/spot-profiler` | POST - Called by audio-worker Lambda |
| └ **Daily Profiler** | `/daily-profiler` | POST - Called by dashboard-analysis-worker Lambda ✅ |
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
| └ Lambda Function (Spot) | `watchme-audio-worker` | Spot analysis |
| └ Call URL (Spot) | ✅ `https://api.hey-watch.me/profiler/spot-profiler` | |
| └ Lambda Function (Daily) | `watchme-dashboard-analysis-worker` | Daily analysis |
| └ Call URL (Daily) | ✅ `https://api.hey-watch.me/profiler/daily-profiler` | |
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

### Endpoint Status

| Endpoint | Method | Status | Description |
|----------|---------|--------|-------------|
| `/health` | GET | ✅ Production | Health check |
| `/spot-profiler` | POST | ✅ Production | Spot profiler analysis (single recording) |
| `/daily-profiler` | POST | ✅ Production (2025-11-15) | Daily profiler analysis (1 day) |
| `/weekly-profiler` | POST | 🚧 Planned | Weekly profiler analysis (7 days) |
| `/monthly-profiler` | POST | 🚧 Planned | Monthly profiler analysis (30 days) |

---

## 🔌 Endpoint Details

### 1. Health Check ✅

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

---

### 2. Spot Profiler ✅

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

### 3. Daily Profiler ✅

**Production** - Since 2025-11-15

```bash
curl -X POST https://api.hey-watch.me/profiler/daily-profiler \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "d067d407-cf73-4174-a9c1-d91fb60d64d0",
    "local_date": "2025-11-15"
  }'
```

**Data Flow**:
```
daily_aggregators.prompt (from Aggregator API)
    ↓ LLM Analysis
daily_results (1 day = 1 record)
```

**Processing Flow**:
1. Fetch prompt from `daily_aggregators.prompt`
2. Execute LLM (Groq/ChatGPT) analysis
   - Input: 1日分のspot_resultsを集約したプロンプト
   - Output: 1日の総合的な心理分析
3. Save result to `daily_results` table

**Response:**
```json
{
  "status": "success",
  "message": "Daily profiler analysis completed (DB save successful)",
  "device_id": "d067d407-cf73-4174-a9c1-d91fb60d64d0",
  "local_date": "2025-11-15",
  "analysis_result": {
    "summary": "1日の総合的な心理状態の説明（日本語）",
    "vibe_score": 15,
    "behavior": "会話, 作業, 休憩",
    "profile_result": {
      "daily_trend": "1日の傾向の説明",
      "key_moments": ["重要な瞬間1", "重要な瞬間2"],
      "emotional_stability": "感情の安定性の説明"
    }
  },
  "database_save": true,
  "processed_at": "2025-11-15T02:00:00.000Z",
  "model_used": "groq/openai/gpt-oss-120b"
}
```

---

### 4. Weekly Profiler 🚧

**Planned** - Phase 4-3

```bash
curl -X POST https://api.hey-watch.me/profiler/weekly-profiler \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "d067d407-cf73-4174-a9c1-d91fb60d64d0",
    "week_start_date": "2025-11-11"
  }'
```

**Data Flow**:
```
weekly_aggregators.prompt (7 days of daily_results)
    ↓ LLM Analysis
weekly_results (1 week = 1 record)
```

**Processing Flow**:
1. Fetch prompt from `weekly_aggregators.prompt`
2. Execute LLM analysis (7日分のdaily_resultsを分析)
3. Save result to `weekly_results` table

---

### 5. Monthly Profiler 🚧

**Planned** - Phase 4-4

```bash
curl -X POST https://api.hey-watch.me/profiler/monthly-profiler \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "d067d407-cf73-4174-a9c1-d91fb60d64d0",
    "year": 2025,
    "month": 11
  }'
```

**Data Flow**:
```
monthly_aggregators.prompt (30 days of daily_results)
    ↓ LLM Analysis
monthly_results (1 month = 1 record)
```

**Processing Flow**:
1. Fetch prompt from `monthly_aggregators.prompt`
2. Execute LLM analysis (30日分のdaily_resultsを分析)
3. Save result to `monthly_results` table

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
  summary TEXT,                       -- Dashboard display summary (Japanese)
  behavior TEXT,                      -- Detected behaviors (comma-separated, 3 items)
  created_at TIMESTAMPTZ DEFAULT NOW(),
  llm_model TEXT NULL,
  PRIMARY KEY (device_id, recorded_at)
);
```

**Saved Fields:**
- `vibe_score`: Psychological score (-100 to +100)
- `summary`: Situation summary in Japanese (2-3 sentences, e.g., "朝食の時間。家族と一緒に食事をしている。")
- `behavior`: 3 key behaviors, comma-separated (e.g., "会話, 食事, 家族団らん")
- `profile_result`: Complete analysis result (JSONB)
  - `summary`: Situation summary (same as TEXT column)
  - `behavior`: Detected behaviors (same as TEXT column)
  - `psychological_analysis`: Mood state, description (Japanese), emotion changes (Japanese)
  - `behavioral_analysis`: Detected activities, behavior pattern (Japanese), situation context (Japanese)
  - `acoustic_metrics`: Speech ratio, loudness, voice stability, pitch variability
  - `key_observations`: Notable findings (Japanese array)
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

### v1.2.0 (2025-11-15)

**Daily Profiler Production Release** 🎉

**Purpose**: Complete daily cumulative analysis pipeline with local_date support

**New Features:**
1. **Daily Profiler Endpoint** (`/daily-profiler`)
   - Analyzes 1 day of spot recordings
   - Fetches prompt from `daily_aggregators` table
   - Saves results to `daily_results` table
   - Parameter: `local_date` (YYYY-MM-DD format)

2. **local_date Support**
   - Added `local_date` column to `spot_results` table
   - Timezone-aware daily aggregation
   - Consistent date handling across the pipeline

3. **Database Schema Updates**
   - New table: `daily_results`
   - Columns: `device_id`, `local_date`, `vibe_score`, `summary`, `behavior`, `profile_result` (JSONB), `llm_model`

4. **Lambda Integration**
   - Called by `watchme-dashboard-analysis-worker` Lambda function
   - Triggered via SQS queue after Daily Aggregator completes
   - Automatic execution on every spot recording completion

**Data Flow:**
```
Spot Profiler completes
  ↓
SQS: dashboard-summary-queue
  ↓
Lambda: dashboard-summary-worker
  ↓
Aggregator API (/aggregator/daily)
  → daily_aggregators table
  ↓
SQS: dashboard-analysis-queue
  ↓
Lambda: dashboard-analysis-worker
  ↓
Profiler API (/profiler/daily-profiler)
  → daily_results table
```

**Benefits:**
- Complete daily psychological analysis available
- Real-time daily summary updates
- Seamless integration with existing pipeline
- Supports multiple timezones via local_date

**Modified Files:**
- `main.py`: Added `DailyProfilerRequest` and `/daily-profiler` endpoint

**Testing:**
- Production deployment completed
- Lambda integration verified
- Database save tested

---

### v1.1.0 (2025-11-13)

**Japanese Output + Behavior Field** 🎉

**Purpose**: Dashboard display enhancement with Japanese text and behavior tags

**Changes:**
1. **Added `summary` and `behavior` columns** to `spot_results` table
   - `summary` (TEXT): Japanese description for dashboard (2-3 sentences)
   - `behavior` (TEXT): 3 key behaviors, comma-separated (e.g., "会話, 食事, 家族団らん")

2. **Updated LLM output format**
   - All text fields now in Japanese (summary, mood_description, behavior_pattern, etc.)
   - Added `behavior` field in LLM response
   - Prompt instructs to prioritize "会話" when speech is detected

3. **Database save enhancement**
   - Extract `summary` from LLM response → save to `summary` column
   - Extract `behavior` from LLM response → save to `behavior` column
   - Full analysis still saved in `profile_result` (JSONB)

**Benefits:**
- Direct display in iOS app/Web dashboard (no translation needed)
- User-friendly Japanese descriptions
- Easy behavior pattern visualization

**Testing:**
- Production test completed with real data
- Database save verified (summary and behavior columns populated)
- Example output:
  - summary: "幼稚園の年長さんが食べ物や遊びについて自分で話している様子です。"
  - behavior: "会話, 食事, 遊び"

**Modified Files:**
- `main.py`: Added summary and behavior extraction

---

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
**Version**: 1.1.0
**Status**: ✅ Production Ready
