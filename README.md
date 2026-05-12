# Flux

A lightweight productivity workspace — boards, columns, cards, and markdown notes.

## Stack

- **Backend:** Django 6 + DRF + PostgreSQL
- **Frontend:** React 19 + Vite 8 + Tailwind v4 + shadcn/ui

## Quick Start

```bash
# Start database
cd docker && docker compose up -d

# Backend
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py runserver

# Frontend
cd frontend
pnpm install
pnpm dev
```

App: http://localhost:3000  
API: http://localhost:8000/api/v1/
# flux
