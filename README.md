# AuraGuard

AuraGuard is a privacy-first, local-first AI layer for personal computing.

## Overview

This MVP establishes the local foundation for a real document ingestion and retrieval pipeline using:

- React + TypeScript + Vite
- FastAPI
- SQLite
- FAISS-ready vector abstraction
- local document processing with no external cloud upload

## Local-first principle

All document processing stays on the local machine by default. No cloud AI providers are used in this MVP.

## Run locally

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

## Project status

The current implementation is the Milestone 1 foundation: environment reporting, SQLite schema, health endpoint, and a basic dashboard with document listing.
