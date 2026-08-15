# DraftWarRoom Setup Guide

Complete setup instructions from zero to running app.

---

## Prerequisites

| Tool | Minimum Version | Check with |
|------|----------------|------------|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| Git | any | `git --version` |

All three should already be installed. If not:
- **Python**: https://www.python.org/downloads/ (check "Add to PATH" during install)
- **Node.js**: https://nodejs.org/ (LTS version, includes npm)

---

## External Accounts & API Keys

### 1. ESPN Fantasy Football (required)

You need your ESPN authentication cookies to access private league data.

**Get your cookies:**
1. Log into your ESPN Fantasy Football league in **Chrome**
2. Open DevTools: press `F12` (or right-click → Inspect)
3. Go to **Application** tab → **Cookies** → `https://www.espn.com`
4. Find and copy these two values:

| Cookie Name | What it looks like |
|------------|-------------------|
| `espn_s2` | Long string (~300 chars), letters and numbers |
| `SWID` | `{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}` (include the curly braces) |

These cookies last several months. If the app stops pulling data, repeat this process to get fresh ones.

### 2. Anthropic API Key (optional — needed for Claude chat)

The chat panel uses Claude to answer free-form fantasy football questions.

1. Go to https://console.anthropic.com and create an account
2. Go to **Settings** → **Billing** → add a payment method
   - API is pay-per-use. Casual chat usage costs pennies per week
   - You can set a monthly spending limit (e.g. $5) under Billing → Limits
3. Go to **API Keys** → **Create Key**
4. Copy the key (starts with `sk-ant-...`)

**Without this key:** Everything works except the Chat tab. All recommendations, scores, waivers, trades, and analytics run locally without any AI calls.

### 3. Sleeper API — no setup needed

Public API, no authentication required. Used automatically for trending players and injury data.

### 4. nflverse — no setup needed

Public data hosted on GitHub. Downloaded automatically for weekly stats and snap counts.

---

## Installation

### Step 1: Create your `.env` file

```bash
cd C:\Users\jeffd\Desktop\Programs\DraftWarRoom\backend
copy ..\.env.example .env
```

Open `backend/.env` in a text editor and fill in your real values:

```env
ESPN_S2=paste_your_espn_s2_cookie_here
ESPN_SWID={paste-your-swid-with-braces}
ESPN_LEAGUE_ID=77367779
ANTHROPIC_API_KEY=sk-ant-paste-your-key-here
DATABASE_URL=sqlite+aiosqlite:///./draftwarroom.db
APP_ENV=development
SECRET_KEY=change-me-in-production
```

**Important:** Never commit this file. It's already in `.gitignore`.

### Step 2: Install Python dependencies

```bash
cd C:\Users\jeffd\Desktop\Programs\DraftWarRoom\backend
pip install -r requirements.txt
```

This installs FastAPI, uvicorn, espn-api, aiosqlite, pandas, anthropic SDK, and other packages.

> **Python 3.14 users:** If pandas or espn-api fails to install, try `pip install --pre -r requirements.txt`. If that still fails, install Python 3.12 or 3.13 alongside and use that version.

### Step 3: Install frontend dependencies

```bash
cd C:\Users\jeffd\Desktop\Programs\DraftWarRoom\frontend
npm install
```

---

## Running the App

You need **two terminals** — one for the backend, one for the frontend.

### Terminal 1: Start the backend

```bash
cd C:\Users\jeffd\Desktop\Programs\DraftWarRoom\backend
uvicorn app.main:app --reload --port 8000
```

On first launch you should see:
```
Applied migration: 001_initial_schema.sql
Scheduler started with background jobs
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Verify it's working: open http://localhost:8000/api/v1/health in your browser. You should see:
```json
{"status": "ok", "app": "DraftWarRoom"}
```

### Terminal 2: Start the frontend

```bash
cd C:\Users\jeffd\Desktop\Programs\DraftWarRoom\frontend
npm run dev
```

This starts the Vite dev server at http://localhost:5173 with automatic proxy to the backend.

### Open the app

Go to **http://localhost:5173** in your browser.

---

## First-Time Data Sync

The app starts with an empty database. You need to pull your league data from ESPN.

### Option A: Use the app UI

Click the **sync button** (circular arrows icon) in the top-right header.

### Option B: Use the API directly

```bash
curl -X POST http://localhost:8000/api/v1/league/sync
```

This takes 10-30 seconds and pulls:
- League settings (name, scoring, roster slots, playoff week)
- All teams (records, points, standings)
- Full rosters (every player on every team)
- Matchup results (scores for completed weeks)
- Draft picks

### Enrich with additional data sources

After the initial ESPN sync, run these to add trending data, advanced stats, and calculated scores:

```bash
# Sleeper: trending adds/drops, injury details
curl -X POST http://localhost:8000/api/v1/sync/sleeper

# nflverse: weekly stats, snap counts, target shares
curl -X POST http://localhost:8000/api/v1/sync/nflverse

# Recalculate composite scores for all players
curl -X POST http://localhost:8000/api/v1/sync/scores

# Calculate power rankings
curl -X POST http://localhost:8000/api/v1/sync/power-rankings

# Run playoff probability simulation (10,000 Monte Carlo sims)
curl -X POST http://localhost:8000/api/v1/sync/playoff-odds
```

**These all run automatically on schedule** once the app is running (every 4-6 hours, with extra Sunday game-day syncs). You only need to trigger them manually the first time.

---

## Cloud Deployment (Optional)

If you want the app running 24/7 instead of just on your laptop:

### Railway (recommended free tier)

1. Push your code to a **GitHub repo** (make sure `.env` is NOT committed)
2. Go to https://railway.app and sign up with GitHub
3. Click **New Project** → **Deploy from GitHub Repo** → select your repo
4. Add a **persistent volume**:
   - Go to your service → Settings → Volumes
   - Mount path: `/app/data`
   - This keeps your SQLite database across deploys
5. Add **environment variables** in the Railway dashboard:
   - `ESPN_S2`, `ESPN_SWID`, `ESPN_LEAGUE_ID`, `ANTHROPIC_API_KEY`
   - `DATABASE_URL=sqlite+aiosqlite:///./data/draftwarroom.db`
   - `APP_ENV=production`
   - `SECRET_KEY=` (generate a random string)
6. Railway auto-detects the `Dockerfile` and builds
7. Your app gets a public URL like `https://draftwarroom-xxxx.up.railway.app`

Railway free tier: 500 hours/month, 1 GB disk — more than enough.

### Docker (local alternative)

If you prefer containers locally:

1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Run:
   ```bash
   cd C:\Users\jeffd\Desktop\Programs\DraftWarRoom
   docker-compose up --build
   ```
3. App runs at http://localhost:8000 (backend + frontend in one container)

---

## Troubleshooting

### "League not synced yet" error
You haven't run the initial sync. POST to `/api/v1/league/sync` or click the sync button.

### ESPN data not loading
- Cookies may have expired. Re-extract `espn_s2` and `SWID` from Chrome DevTools.
- Make sure `SWID` includes the curly braces: `{XXXXXXXX-XXXX-...}`
- Verify your league ID is correct (visible in the ESPN Fantasy URL).

### Chat not responding
- Check that `ANTHROPIC_API_KEY` is set in `backend/.env`
- Verify you have billing set up at console.anthropic.com
- The key should start with `sk-ant-`

### pip install fails on Python 3.14
Some packages may not have 3.14 wheels yet. Options:
- Try `pip install --pre -r requirements.txt`
- Install Python 3.12 from python.org (can coexist with 3.14)
- Use `py -3.12 -m pip install -r requirements.txt` and `py -3.12 -m uvicorn app.main:app --reload`

### Frontend shows blank page
- Make sure the backend is running on port 8000
- Check the browser console (F12) for errors
- Vite proxy expects the backend at `http://localhost:8000`

### Stale data
Click the sync button or wait for the next scheduled sync. Syncs run automatically:
- Every 6 hours (league data)
- Every 4 hours (Sleeper trending)
- Daily at 5 AM (nflverse stats)
- Hourly on Sundays during games
