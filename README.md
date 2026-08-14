# Travel Companion

A multilingual AI travel companion. It recommends destinations from a vibe and a
budget, searches real flights, builds day-by-day itineraries, and exports the plan
to your calendar. Answers in whatever language you write in — mostly Indonesian
and English.

> **Work in progress.** The backend is complete through phase 3 — agent core,
> knowledge base, and bring-your-own-key. The web app is next. See the
> [roadmap](#roadmap).

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
| `search_knowledge` | Retrieval over the travel knowledge base |

Adding a capability means adding one decorated function, not another branch in the
conversation pipeline.

## Knowledge base

`search_knowledge` queries a ChromaDB collection built from Wikivoyage guides plus
curated cost and seasonal data. Embeddings run locally in-process (ONNX
all-MiniLM-L6-v2), which is the load-bearing choice: generation is
bring-your-own-key, so retrieval must not need an API key of its own, or the server
would still pay per query.

Retrieval is a tool, not a step in front of every message — always retrieving wastes
latency on greetings and drags irrelevant passages into context.

```bash
cd apps/api
python -m scripts.build_index            # curated + Wikivoyage
python -m scripts.build_index --offline  # curated only
```

The index is built into the Docker image at build time. Cloud Run's filesystem is
ephemeral and scales to zero, so a runtime index would be rebuilt on every cold
start.

## Bring your own key

Without a key you get a small daily allowance on the server's key. Supply your own
and the limit disappears — the cost moves to you.

```
POST /api/chat/stream
X-LLM-Api-Key: <your key>       # optional
X-LLM-Provider: openai          # optional; defaults to the server's provider
```

Your key is never stored, never logged, never echoed back, and never sent anywhere
except the provider you chose. It exists for the duration of one request. Those
properties are asserted in `tests/test_access.py`, not just claimed here.

## Running locally

```bash
pnpm install

# API — uv is much faster than pip
cd apps/api
uv venv --python 3.13
uv pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env          # fill in your API keys
uvicorn src.api:app --reload  # http://127.0.0.1:8000/docs

python -m scripts.build_index # build the knowledge index (once)
pytest                        # 76 tests, no network needed
```

The web app is not runnable yet — the Next.js scaffold lands in phase 4.

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 0 | Monorepo setup | ✅ |
| 1 | Agent core: LiteLLM, tool-calling, real streaming | ✅ |
| 2 | RAG: Wikivoyage → ChromaDB, retrieval tool | ✅ |
| 3 | Bring-your-own-key + rate limiting | ✅ |
| 4 | Landing page, design system, seeded tool calls | ⬜ |
| 5 | Itinerary + calendar export (`.ics`) | ⬜ |
| 6 | Shareable trip board | ⬜ |
| 7 | Deploy + observability | ⬜ |

Phase 4 is specified in [`docs/design-brief.md`](docs/design-brief.md) and
[`docs/phase-4-plan.md`](docs/phase-4-plan.md). The landing page pairs the live agent
with a structured search widget: the form does not navigate to a results page, it
seeds the agent with a validated tool call and the answer streams in place.

## Earlier iterations

This continues work from two separate repositories. They are archived rather than
deleted — their code seeded this monorepo, and their history is still readable there:

- [`my-travel-agent`](https://github.com/shendyppy/my-travel-agent) — FastAPI backend,
  first agent built on regex intent detection
- [`my-travel-agent-app`](https://github.com/shendyppy/my-travel-agent-app) — React + Vite chat UI

The move to a monorepo was driven by the API contract: copying `FlightInfo` by hand
from Pydantic into TypeScript was drift waiting to happen. Types are generated from
the OpenAPI schema now.
