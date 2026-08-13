# Travel Companion

A multilingual AI travel companion. It recommends destinations from a vibe and a
budget, searches real flights, builds day-by-day itineraries, and exports the plan
to your calendar. Answers in whatever language you write in — mostly Indonesian
and English.

> **Work in progress.** Phase 1 (agent core) is done. See the [roadmap](#roadmap).

## Layout

```
travel-companion/
├─ apps/
│  ├─ api/        FastAPI — agent loop, tools, flight integrations
│  └─ web/        Next.js — landing, chat, trip board
└─ packages/
   ├─ types/      TypeScript types generated from the FastAPI OpenAPI schema
   └─ ui/         shared design system
```

## Stack

| Layer | Technology |
|---|---|
| Web | Next.js (App Router), TypeScript, Tailwind v4, shadcn/ui, TanStack Query |
| API | FastAPI, Python 3.13, LiteLLM, Redis |
| LLM | Provider-agnostic via LiteLLM — Gemini, OpenAI, Anthropic, GLM |
| Flight data | Amadeus + Google Flights (RapidAPI) |
| Deploy | Vercel (web) · Cloud Run (api) · Upstash (Redis) |

## How the agent works

The agent is a tool-calling loop. The model decides what the user wants by choosing
which tool to call; there is no intent detection by regex anywhere.

```
user message ──> model ──┬─> answers directly            ──> done
                         └─> requests tools ──> run them ──> feed results back ──┐
                                          ▲                                      │
                                          └──────────────────────────────────────┘
```

Current tools:

| Tool | Purpose |
|---|---|
| `lookup_place` | City or nickname → IATA airport codes |
| `resolve_dates` | Vague timing ("next long weekend") → concrete dates |
| `search_flights` | Real flights for a specific date |
| `search_flights_flexible` | Cheapest flight across a date range |
| `recommend_destinations` | Suggestions by budget, style, and season |
| `get_destination_info` | Cost breakdown and seasonal detail for one place |

Adding a capability means adding one decorated function, not another branch in the
conversation pipeline.

## Running locally

```bash
pnpm install

# API — uv is much faster than pip
cd apps/api
uv venv --python 3.13
uv pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env          # fill in your API keys
uvicorn src.api:app --reload  # http://127.0.0.1:8000/docs

pytest                        # 49 tests, no network needed
```

The web app is not runnable yet — the Next.js scaffold lands in phase 4.

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 0 | Monorepo setup | ✅ |
| 1 | Agent core: LiteLLM, tool-calling, real streaming | ✅ |
| 2 | RAG: Wikivoyage → ChromaDB, retrieval tool | ⬜ |
| 3 | Bring-your-own-key + rate limiting | ⬜ |
| 4 | Landing page + design system | ⬜ |
| 5 | Itinerary + calendar export (`.ics`) | ⬜ |
| 6 | Shareable trip board | ⬜ |
| 7 | Deploy + observability | ⬜ |

## Earlier iterations

This continues work from two separate repositories. They are archived rather than
deleted — their code seeded this monorepo, and their history is still readable there:

- [`my-travel-agent`](https://github.com/shendyppy/my-travel-agent) — FastAPI backend,
  first agent built on regex intent detection
- [`my-travel-agent-app`](https://github.com/shendyppy/my-travel-agent-app) — React + Vite chat UI

The move to a monorepo was driven by the API contract: copying `FlightInfo` by hand
from Pydantic into TypeScript was drift waiting to happen. Types are generated from
the OpenAPI schema now.
