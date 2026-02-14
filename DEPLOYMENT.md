# Deployment Guide

Get Wasp-OS running end-to-end with the frontend on Vercel and backend on Render.

## Quick Start (Demo Mode)

The frontend works out of the box in **demo mode** without a backend:

1. Push your repo to GitHub and connect it to [Vercel](https://vercel.com).
2. Set **Root Directory** to `frontend` in Project Settings → General.
3. Deploy. Visit the site, click **Try Demo**, and explore with mock data.

## Full Deployment (Frontend + Backend)

### 1. Database (Supabase or Neon)

Create a PostgreSQL database with pgvector. [Supabase](https://supabase.com) (free tier) works well:

- Create a project
- Copy the **Connection string** (URI format: `postgresql://...`)

For Supabase, use the **transaction** pooler URL (port 6543) if using PgBouncer.

### 2. Backend on Render

1. Go to [Render](https://render.com) and connect your GitHub repo.
2. **New → Blueprint** and select this repo. Render will read `render.yaml`.
3. Or **New → Web Service**, select the repo, and:
   - **Runtime**: Docker
   - **Dockerfile Path**: `./Dockerfile`
   - **Instance Type**: Free

4. Set environment variables:

   | Variable        | Value                                           |
   | --------------- | ----------------------------------------------- |
   | `DATABASE_URL`  | Your PostgreSQL connection string               |
   | `SECRET_KEY`    | A random string (e.g. from `openssl rand -hex 32`) |
   | `CORS_ORIGINS`  | Your Vercel URL (e.g. `https://your-app.vercel.app`) |
   | `ANTHROPIC_API_KEY` | Optional, for Ghostwriter AI features       |

5. Deploy. Note the backend URL (e.g. `https://waspos-backend.onrender.com`).

### 3. Run Migrations

Apply the schema to your database:

```bash
cd backend
# Set DATABASE_URL in .env or export it
alembic upgrade head
```

Or run migrations from Render’s shell if available.

### 4. Seed Demo User (Optional)

```bash
cd backend
python scripts/seed_mock_data.py
# Use lead@wasp.vc / testpassword123 to log in
```

### 5. Frontend on Vercel

1. In Vercel Project Settings → **Environment Variables**, add:

   | Variable                 | Value                         |
   | ------------------------ | ----------------------------- |
   | `NEXT_PUBLIC_API_URL`    | Your Render backend URL       |

2. Redeploy the frontend.

### 6. Summary

- **Frontend (Vercel)**: Root directory `frontend`, `NEXT_PUBLIC_API_URL` = backend URL.
- **Backend (Render)**: `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS` = Vercel URL.
- **Database**: Supabase or any PostgreSQL with pgvector.
