# Travel Companion

A multilingual AI travel companion. It recommends destinations from a vibe and a
budget, searches real flights, builds day-by-day itineraries, and exports the plan
to your calendar. Answers in whatever language you write in — mostly Indonesian
and English.

> **Work in progress.** Agent core, knowledge base, bring-your-own-key, the landing
> page, and the flight results page are in. The companion dock and calendar export are
> next. See the [roadmap](#roadmap).

## Layout

```
travel-companion/
├─ apps/
│  ├─ api/        FastAPI — agent loop, tools, flight integrations
│  └─ web/        Next.js — landing, chat, trip board
└─ packages/
   └─ types/      TypeScript types generated from the FastAPI OpenAPI schema
```

Components are grouped by what they are, not by which page they landed on first:

```
apps/web/src/components/
├─ ui/            atoms — shadcn primitives, managed by its CLI
├─ molecules/     one job, composes atoms, no domain knowledge
├─ organisms/     a self-contained block that means something in this product
├─ templates/     page compositions
├─ illustration/  drawn scenes
└─ i18n/          the message provider
```

What separates a molecule from an organism is behaviour, not size. `ToolResult`
is twenty lines and is an organism, because it decides which card a given tool
call deserves — that is knowledge about this product. `Price` is the same length
and is a molecule, because it renders a number and knows nothing else.

The earlier layout named folders after pages, which made "is this reused?"
unanswerable at a glance. It was being reused: the price treatment existed in six
copies, two of them disagreeing about whether to round.

`templates/` holds the `*Client` components. They are page compositions but they
still own their data, so they keep the honest name — splitting a data-free
template out of them is worth doing when a second page wants the same layout, and
not before.

## Motion

One rule: **motion must be caused.** Either the reader caused it — a press, a
hover, a scroll — or it happens once on arrival. Nothing loops in the corner of the
eye and nothing moves while you are reading it. Every primitive below is a Tailwind
`@utility` in `globals.css`, built on the duration and easing tokens, and every one
honours `prefers-reduced-motion`.

| Utility | What it does |
|---|---|
| `reveal` | a section arriving as it is scrolled to, once |
| `stagger` | direct children cascading 60ms apart |
| `draw` | a stroke drawing itself; `pathLength="1"` fits any curve |
| `travel` | movement along an `offset-path` |
| `pop` | a spring-overshoot entrance, for things that should land with weight |
| `lift` | 2px and a hue-tinted shadow on hover |
| `pressable` | 1px of travel on `:active` |
| `grain` | a fixed 2.5% noise layer, so flat fills stop reading as a swatch |

Two things worth knowing before editing this. `travel` takes its `offset-path` from
the same `d` the shape is drawn from — never a second copy, or the plane flies
beside the line instead of along it. And `DemoSection`'s sticky panel works only
because `useInView` fires once and disconnects, leaving `reveal` at `transform:
none`; a non-none transform on an ancestor becomes the containing block and
silently kills `position: sticky`.

## Stack

| Layer | Technology |
|---|---|
| Web | Next.js (App Router), TypeScript, Tailwind v4, shadcn/ui, TanStack Query |
| Type | Plus Jakarta Sans + JetBrains Mono, self-hosted via `next/font` |
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

## Languages

The UI ships in Indonesian and English, chosen by the URL — `/id` and `/en`. A visitor
with no locale in the path is redirected once based on `Accept-Language`, and after
that the URL wins, so a link someone shares opens in the language it was shared in.

There is no i18n library. Two locales with static dictionaries need a typed object
lookup and a string replace, and `en.json` is typed against `id.json` so a missing
translation fails the build rather than rendering `undefined`.

The agent's own replies were always bilingual — it answers in whatever language you
write to it. Only the chrome needed translating.

## Running locally

**Node 20+ is required** and the version in `.nvmrc` is what this is developed against.
Older Node fails with `Unexpected token '??='` when Next parses its own source.

```bash
nvm use          # or fnm use — reads .nvmrc
pnpm install

# One-time API setup — uv is much faster than pip
cd apps/api
uv venv --python 3.13
uv pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env               # fill in your API keys
uv run python -m scripts.build_index
```

Then, from the repo root, one command runs both services:

```bash
pnpm dev         # API on :8000, web on :3000
```

`apps/api` is a workspace package with a `package.json` that exists purely so pnpm and
turbo can see it. Without that file, `pnpm dev` silently starts only Next and the
frontend talks to nothing.

If `pnpm dev` ever dies with `ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY`, two
different pnpm builds have touched `node_modules` — on Windows `C:\Program
Files\nodejs` is an nvm symlink, so changing Node version changes pnpm with it. Run
`nvm use` and `pnpm install` once, deliberately. `verifyDepsBeforeRun: false` in
`pnpm-workspace.yaml` stops pnpm trying to fix this by itself mid-`dev`, which it
cannot do without a TTY that turbo does not give it.

`pnpm dev` deliberately does not go through turbo. It runs `pnpm -r --parallel run
dev` instead, because turbo used to crash on it: exit code `3221226505` right after
the version banner and no task output at all — `0xC0000409`,
`STATUS_STACK_BUFFER_OVERRUN`, turbo's own binary aborting rather than a task
failing. It only happened on persistent tasks, which is why `pnpm build` and `pnpm
typecheck` were never affected and still use turbo, where its caching actually pays
for itself. For `dev` it was only ever spawning two processes, and pnpm does that
without a native binary in the way.

```bash
pnpm --filter @travel/api test   # 142 tests, no network needed
pnpm typecheck
pnpm build
```

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 0 | Monorepo setup | ✅ |
| 1 | Agent core: LiteLLM, tool-calling, real streaming | ✅ |
| 2 | RAG: Wikivoyage → ChromaDB, retrieval tool | ✅ |
| 3 | Bring-your-own-key + rate limiting | ✅ |
| 4 | Landing page, design system, seeded tool calls | ✅ |
| 4b | `/flights` results page — full list, filters, sort | ✅ |
| 4c | Colour system, illustrations, motion, landing narrative | ✅ |
| 4d | Indonesian + English, OG images, sitemap, onboarding tour | ✅ |
| 4e | Brand mark, real typeface, motion system, atomic components | ✅ |
| 5 | Companion dock: the agent reads the page you are on | ⬜ |
| 6 | Itinerary + trip board + calendar export (`.ics`) | ⬜ |
| 7 | Google sign-in + Calendar sync (OAuth, two-way) | ⬜ |
| 8 | Deploy + observability | ⬜ |

Phase 4 is specified in [`docs/design-brief.md`](docs/design-brief.md) and
[`docs/phase-4-plan.md`](docs/phase-4-plan.md). The landing page pairs the live agent
with a structured search widget: the form seeds the agent with a validated tool call
and the answer streams in place.

Phase 4b adds the one exception. A flight search on a fixed date navigates to
`/flights` and renders every option the provider returned, filterable by airline,
stops, and departure time — because twenty near-identical fares are a table, and a
hero morphing into a table is a worse version of a page that can just exist. It is the
same tool with the same arguments either way; only the surface differs. Flexible dates,
inspiration, and free text still answer in the hero.

Two ceilings, deliberately different: `search_flights` (the tool) truncates to eight
results because those are billed as model context, while `GET /api/flights/search`
returns everything. A page has no tokens to budget.

## Earlier iterations

This continues work from two separate repositories. They are archived rather than
deleted — their code seeded this monorepo, and their history is still readable there:

- [`my-travel-agent`](https://github.com/shendyppy/my-travel-agent) — FastAPI backend,
  first agent built on regex intent detection
- [`my-travel-agent-app`](https://github.com/shendyppy/my-travel-agent-app) — React + Vite chat UI

The move to a monorepo was driven by the API contract: copying `FlightInfo` by hand
from Pydantic into TypeScript was drift waiting to happen. Types are generated from
the OpenAPI schema now.
