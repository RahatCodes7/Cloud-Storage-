# Trove

A self-hosted file storage dashboard that uses Telegram as its backend — upload, browse, preview, download, and share files through a modern web UI. Every file is stored in a Telegram supergroup with Forum/Topics enabled.

## Architecture

```
Browser (React + Vite)
    │ HTTPS / JSON
    ▼
FastAPI Backend (Python)
    │   └── SQLite (local index/cache)
    │ MTProto (Kurigram)
    ▼
Telegram Supergroup (Forum with Topics)
    ├── Topic: user_1's files
    ├── Topic: user_2's files
    └── ...
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- A Telegram account (the "storage" account)
- A Telegram API ID and Hash (from https://my.telegram.org)

## Quick Start (Local Development)

### 1. Clone and set up backend

```bash
git clone <repo-url>
cd trove/backend
pip install -r requirements.txt
```

### 2. Generate Telegram session

```bash
python ../scripts/generate_session.py
```
This will prompt for your phone number and OTP. Save the session string it outputs.

### 3. Create a Telegram supergroup

1. Open Telegram and create a **New Group**
2. Add at least 2 members (you can remove them later)
3. Convert to **Supergroup** (group info → ... → Convert)
4. Enable **Topics** (group info → Topics → Enable)
5. Get the chat ID by forwarding a message to **@getidsbot** or checking the URL

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your Telegram credentials:

| Variable | Value |
|----------|-------|
| `TELEGRAM_API_ID` | From my.telegram.org |
| `TELEGRAM_API_HASH` | From my.telegram.org |
| `TELEGRAM_SESSION_STRING` | From the session generator script |
| `TELEGRAM_STORAGE_CHAT_ID` | Your supergroup ID (e.g. -1001234567890) |
| `JWT_SECRET` | Run: `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `ALLOW_PUBLIC_REGISTRATION` | `true` for open sign-up, `false` for invite-only |
| `CORS_ORIGINS` | Your frontend URL (e.g. http://localhost:5173) |

### 5. Start the backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Deploy to Production

### Backend → Render

[Render](https://render.com) offers a free tier that works well for Trove.

#### Step 1: Push your code to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/trove.git
git push -u origin main
```

#### Step 2: Create a Render Web Service

1. Go to [dashboard.render.com](https://dashboard.render.com) → **New +** → **Web Service**
2. Connect your GitHub repo
3. Fill in the form:

   | Field | Value |
   |-------|-------|
   | **Name** | `trove` |
   | **Environment** | `Python` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | **Plan** | Free |

#### Step 3: Add environment secrets

In the Render dashboard, go to **Environment** and add these secrets:

| Key | Value |
|-----|-------|
| `TELEGRAM_API_ID` | From my.telegram.org |
| `TELEGRAM_API_HASH` | From my.telegram.org |
| `TELEGRAM_SESSION_STRING` | Your session string |
| `TELEGRAM_STORAGE_CHAT_ID` | Your supergroup ID |
| `JWT_SECRET` | Random 64-char hex string |
| `ALLOW_PUBLIC_REGISTRATION` | `true` or `false` |
| `CORS_ORIGINS` | Your Vercel frontend URL (e.g. https://trove.vercel.app) |
| `MAX_UPLOAD_MB` | `2000` |

> ⚠️ **Never commit your secrets.** Use Render's Environment Variables or a `.env` file locally only.

#### Step 4: Deploy

Click **Deploy**. Render will build and start your service. The first deploy takes 2–3 minutes.

Your backend will be at: `https://trove.onrender.com`

#### Free Tier Notes

- Render spins down after 15 minutes of inactivity
- First request after idle will take ~30 seconds (cold start)
- 750 free instance-hours per month
- SQLite data is **ephemeral** — the app uses Telegram snapshots for persistence

---

### Frontend → Vercel

[Vercel](https://vercel.com) is free for personal projects and auto-deploys from GitHub.

#### Step 1: Push to GitHub

Same repo as above — the frontend lives in `frontend/`.

#### Step 2: Create a Vercel project

1. Go to [vercel.com](https://vercel.com) → **Add New** → **Project**
2. Import your GitHub repo
3. Configure:

   | Setting | Value |
   |---------|-------|
   | **Framework Preset** | `Vite` |
   | **Root Directory** | `frontend` |
   | **Build Command** | `npm run build` |
   | **Output Directory** | `dist` |

#### Step 3: Add environment variable

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://trove.onrender.com` (your Render backend URL) |

#### Step 4: Deploy

Click **Deploy**. Vercel will build and deploy your frontend.

Your frontend will be at: `https://trove.vercel.app`

#### Step 5: Update CORS on Render

Go back to your Render dashboard and update `CORS_ORIGINS`:

```
CORS_ORIGINS=https://trove.vercel.app
```

Then **Manual Deploy** → **Deploy** on Render.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/auth/register` | Register (if enabled) |
| `POST` | `/api/auth/login` | Login, returns JWT |
| `POST` | `/api/auth/logout` | Logout |
| `GET` | `/api/auth/me` | Current user |
| `GET` | `/api/files` | List files |
| `POST` | `/api/files` | Upload file |
| `GET` | `/api/files/{id}/download` | Download file |
| `GET` | `/api/files/{id}/preview` | Stream/preview file |
| `PATCH` | `/api/files/{id}` | Rename / move |
| `DELETE` | `/api/files/{id}` | Soft delete (to trash) |
| `DELETE` | `/api/files/{id}/permanent` | Permanent delete |
| `POST` | `/api/files/{id}/restore` | Restore from trash |
| `POST` | `/api/files/{id}/share` | Create share link |
| `GET` | `/api/stats` | Storage statistics |

## Tech Stack

- **Backend:** Python, FastAPI, Kurigram (Pyrogram fork), SQLite, SQLAlchemy
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, React Query, React Router
- **Storage:** Telegram MTProto API (free, unlimited file storage)

## License

MIT
