# Phase 4 — landing page, design system, and the seeded-tool hero

Companion to [`design-brief.md`](./design-brief.md). The brief says what to build and
why it should look the way it does; this says in what order, what it costs, and what
can go wrong.

---

## What changed, and why this document exists

The original phase 4 scope was "landing page + design system", where the landing page
was a hero chat box with three cards under it. That page is honest about the product
but sells it badly: a visitor who does not already know what to type sees a blinking
cursor, and the page reads as a wrapper around a model rather than as a travel
product.

The revised scope keeps the live agent in the hero — that part was right and is
non-negotiable — and adds the structured-search affordance an Indonesian traveller
already knows how to use. The two are not alternatives. The form seeds the agent.

**That one sentence is the whole phase.** Everything below is in service of making a
form submission and a typed sentence arrive at the same place.

### What this phase is not

No hotels, trains, cars, insurance, or attraction tickets. There is no backend for any
of them and there will not be one in phase 4. The product sits upstream of the OTA: it
decides what is worth booking and hands off via `providers/booking_links.py`.

When someone asks "kenapa nggak ada hotel?", the answer is not "belum sempat" — it is
that a recommendation engine that also takes a booking fee has a conflict of interest,
and this one does not. Write that down somewhere on the page.

---

## Backend work

Three changes. The first is load-bearing; the other two are small.

### 1. Seeded tool calls — `ChatRequest.seed`

**Problem.** The hero's flight form knows exactly what it wants: `search_flights` with
these five arguments. Today the only way in is `ChatRequest.message`, so the client
would have to compose a sentence ("cari penerbangan Jakarta ke Bali tanggal…") and
*hope* the model picks the right tool with the right arguments. That is a lossy
round-trip through natural language for information that was already structured, and
it will be wrong often enough to be embarrassing in a hero.

**Change.**

```python
class ToolSeed(BaseModel):
    tool: str
    arguments: dict[str, Any]

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    seed: Optional[ToolSeed] = None      # new
```

The agent loop, when a seed is present, runs the tool **before the first model turn**
and writes the call and its result into the transcript in the same shape the model
would have produced itself:

```
seed ──> validate ──> dispatch ──> append assistant(tool_calls=[…])
                                   append tool(result)
                                   ──> model narrates ──> normal loop continues
```

The SSE stream emits the same `tool_start` / `tool_result` events as any other tool
call, so the frontend needs no special case — `ToolActivity` renders a seeded flight
search identically to a model-chosen one.

Appending it as though the model called it is the important detail. It means turn two
onwards has no idea a seed happened, follow-up questions ("yang lebih pagi ada?")
resolve against it naturally, and there is no second code path to keep in sync.

**Rules, and these are the security surface of the whole phase:**

| Rule | Why |
|---|---|
| Allowlist: `search_flights`, `search_flights_flexible`, `recommend_destinations`, `get_destination_info` | `seed` is client-controlled tool dispatch. Without an allowlist, any caller can invoke anything the registry ever gains. |
| Arguments validated against the registered JSON Schema before dispatch | The schemas already exist in `registry.py`. Add `registry.validate(name, args)` next to `dispatch`; do not hand-roll per-tool checks. |
| Validation failure ⇒ drop the seed, keep the message, log it | Never 500 a hero. A degraded answer beats an error page. |
| A seeded request consumes daily quota like any other | It costs a model turn. Free tool calls would be a hole in `access.py`. |
| `message` stays required | The seed is context, not a replacement for intent. The client sends both: the form's own human-readable summary as `message`, the structured call as `seed`. |

Roughly one new module plus a branch in `loop.py`. Tests belong next to
`test_agent_loop.py` and should cover: seed dispatched and narrated, seed rejected by
allowlist, seed with malformed arguments, seed whose tool fails at the provider.

### 2. `GET /api/deals` — cached fare rail

A live `DealRail` would be 15 destinations × up to 7 provider calls per page view.
That is not a rate-limit concern, it is a bill.

```
GET /api/deals?origin=CGK
→ { origin, updated_at, deals: [ { city, iata, price_idr, departure_date }, … ] }
```

- Redis, key `deals:{origin}`, TTL 12h, serve stale while revalidating.
- Warmed by a scheduled job over the top 5 Indonesian origins (CGK, SUB, DPS, KNO,
  UPG) × 15 destinations = 75 route lookups per refresh. Everything else is a cold
  miss.
- **Cold miss returns an empty list, not a fabricated price.** The rail then renders
  cards with a "cek harga" action instead of a number. This is the honest fallback and
  it needs to be designed, not bolted on — see constraint 9 in the brief.
- `updated_at` is part of the contract because the card displays it.

### 3. `GET /api/destinations` — curated set and facet vocabularies

The `InspirationGrid` and `ExploreFacets` need the 15 destinations plus the
`TravelType` / `BudgetCategory` / `Season` / region vocabularies. All of it is already
in memory in `destination_data.py`. Serving it beats hardcoding the enums in the
frontend, which would drift the moment a destination is added.

Types flow to `packages/types` through the existing OpenAPI generation — same as
`FlightInfo`. That is the reason the monorepo exists; use it.

---

## Frontend work

`apps/web` currently holds only `src/components` carried over from the old Vite app.
There is no `package.json`, no App Router, no build. Phase 4 starts at the scaffold.

| Step | Scope | Depends on |
|---|---|---|
| **4a — Foundation** | Next.js App Router scaffold, Tailwind v4 with the tokens from `tokens.css`, shadcn re-init, port the existing `ChatBubble` / `FlightCard` / `ChatInput` to the new tokens, wire `GET /api/destinations` | backend #3 |
| **4b — The spine** | `SearchCommandBar` with all three modes, `FlightSearchForm`, `ExploreFacets`, `HeroLiveAnswer`, streaming wired to `/api/chat/stream`, `ToolActivity` | backend #1 |
| **4c — Density** | `DealRail`, `InspirationGrid`, `BudgetBandPicker`, `OriginPicker` | backend #2 |
| **4d — Below fold** | Capability cards, trip board preview, technical section, SEO + Open Graph | 4a |
| **4e — Mobile** | Command bar collapse, rails to snap-scroll, nav merge | 4b, 4c |

Build 4b before 4c. The density layer is the part that is fun to build and the part
that is worthless if the hero hand-off does not work — `DealCard` and
`InspirationTile` both submit *through* the command bar, so they have nothing to
submit to until it exists.

`/chat`, `/trip/[id]`, and the `ApiKeyDialog` stay in scope as the brief describes
them; nothing above changes those screens.

---

## Risks

**Client-controlled tool dispatch.** `seed` is the first endpoint where a caller
chooses which internal function runs. Allowlist and schema validation are not
hardening to add later — they ship in the same commit as the field, or the field does
not ship.

**Cache cost drift.** 75 route lookups per refresh is fine at 12h. It is not fine at
1h, and it is not fine if the origin list grows to twenty cities. Whoever changes the
TTL or the origin list should have to notice they are changing a bill; put the numbers
in a constant with a comment, not spread across a config file.

**The hero has to survive a bad first request.** Providers time out, routes have no
flights, and the very first thing a recruiter does is type something odd. The resolved
state includes "tidak ketemu" and "gagal, ini kenapa" as normal outcomes. The brief
already says failure states get real design; the hero is where that matters most,
because it is the only one a visitor is guaranteed to see.

**Layout jump on morph.** Empty command bar → streaming answer → result cards is a
large height change on the most visible element of the page. Reserve height for the
resolved state, or the page shifts under the reader exactly as the first token
arrives.

**Density becoming clutter.** Three entry points (command bar, deals, inspiration) all
compete for the same job. If a user cannot tell in two seconds which one to use, the
Traveloka influence has been copied rather than borrowed. The mitigation is hierarchy,
not removal: the command bar is the page's one primary action, and the rails below are
answers you can browse, not a second search UI.

---

## Definition of done

- A visitor who lands on `/` and touches nothing still sees real destination prices.
- A visitor who fills the flight form sees a real fare, sourced from a real provider,
  streaming in place, without leaving the page.
- A visitor who types a sentence gets the identical components.
- A visitor on a phone gets all three without a horizontal scrollbar.
- Nothing on the page is clickable that does not work.
