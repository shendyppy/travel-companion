# Travel Companion

AI travel companion berbahasa Indonesia: kasih rekomendasi destinasi dari vibe & budget,
cariin penerbangan real-time, susun itinerary per hari, lalu export agendanya ke kalender.

> **Status: dalam pengerjaan.** Fase 0 (setup monorepo) selesai. Lihat [Roadmap](#roadmap).

## Struktur

```
travel-companion/
├─ apps/
│  ├─ api/        FastAPI — agent, tool, integrasi penerbangan
│  └─ web/        Next.js — landing, chat, trip board
└─ packages/
   ├─ types/      tipe TS hasil generate dari OpenAPI FastAPI
   └─ ui/         design system bersama
```

## Stack

| Layer | Teknologi |
|---|---|
| Web | Next.js (App Router), TypeScript, Tailwind v4, shadcn/ui |
| API | FastAPI, Python 3.11+, LiteLLM, Redis |
| LLM | Provider-agnostic lewat LiteLLM — Gemini, OpenAI, Anthropic, GLM |
| Data penerbangan | Amadeus + Google Flights (RapidAPI) |
| Deploy | Vercel (web) · Cloud Run (api) · Upstash (Redis) |

## Jalanin di lokal

```bash
pnpm install

# API
cd apps/api
cp .env.example .env          # isi API key-nya
pip install -r requirements.txt
uvicorn src.api:app --reload  # http://127.0.0.1:8000/docs
```

Web belum bisa dijalanin — scaffold Next.js-nya masuk di Fase 2.

## Roadmap

| Fase | Isi | Status |
|---|---|---|
| 0 | Setup monorepo, salin sumber dari dua repo lama | ✅ |
| 1 | Agent core: LiteLLM + tool-calling + streaming beneran | ⬜ |
| 2 | Landing page + design system | ⬜ |
| 3 | Itinerary + export kalender (`.ics`) | ⬜ |
| 4 | Trip board yang bisa di-share | ⬜ |
| 5 | Deploy + rate limiting | ⬜ |

## Iterasi sebelumnya

Project ini lanjutan dari dua repo terpisah. Repo-repo itu diarsipkan, bukan dihapus —
kodenya jadi bahan awal monorepo ini, dan history-nya masih kebaca di sana:

- [`my-travel-agent`](https://github.com/shendyppy/my-travel-agent) — backend FastAPI, agent
  pertama dengan intent-detection berbasis regex
- [`my-travel-agent-app`](https://github.com/shendyppy/my-travel-agent-app) — chat UI React + Vite

Alasan pindah ke monorepo: kontrak API antara frontend dan backend mulai sering berubah,
dan nyalin `FlightInfo` manual dari Pydantic ke TypeScript itu drift yang nunggu kejadian.
Sekarang tipenya di-generate dari skema OpenAPI.
