# Wasp-OS: Investment Operating System for Venture Capital

A comprehensive platform for VC firms to streamline deal flow, institutional memory, and investment committee processes.

## Architecture

```
wasp-os/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration, security
│   │   ├── db/             # Database connections
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   │       ├── memory/     # PDF parsing, vector embeddings
│   │       ├── ghostwriter/# LLM memo generation
│   │       └── courage/    # Blind polling, divergence
│   ├── scripts/            # CLI tools
│   └── tests/
├── frontend/               # Next.js React frontend
│   └── src/
│       ├── app/           # Next.js app router
│       ├── components/    # React components
│       │   ├── ui/        # Shadcn UI components
│       │   ├── radar/     # Heat maps, blind-spot viz
│       │   └── pipeline/  # Deal pipeline components
│       ├── lib/           # Utilities
│       ├── hooks/         # Custom React hooks
│       └── types/         # TypeScript types
└── docker-compose.yml
```

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: Next.js 14 + Tailwind CSS + Shadcn UI
- **Database**: PostgreSQL + pgvector (via Supabase)
- **LLM**: Anthropic Claude 3.5 Sonnet via LangChain
- **Auth**: Clerk (per-fund private instances)

## Quick Start

### Demo Mode (No Backend)

Deploy the frontend to Vercel and use **Try Demo** on the login page. You'll explore the Deal Pipeline with mock data—no backend or database required. See [DEPLOYMENT.md](./DEPLOYMENT.md) for full deployment instructions.

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Core Features

### Phase 1: The Wedge
- **PDF Uploader**: Ingest pitch decks, extract Team/TAM/Moat/Traction
- **Historical Indexer**: CLI to vectorize past IC memos
- **Ghostwriter**: Auto-draft memos with contradiction flagging

### Phase 2: Internal Dissent
- **Blind IC Polling**: Pre-meeting conviction scoring (1-10)
- **Divergence View**: Highlight score gaps between partners
- **Red Flag Tracking**: Anonymous concern logging

## Multi-tenancy

All data is siloed by `firm_id` ensuring complete isolation between VC firms.
