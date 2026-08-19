# Design brief — Travel Companion

Paste this into Claude Design. It describes a product whose backend already exists,
so the constraints in here are real rather than hypothetical: every state listed
below corresponds to something the API actually emits.

---

## What this is

A multilingual AI travel companion for Indonesian travellers. You tell it the kind
of trip you want — a vibe, a budget, a rough time of year — and it recommends
destinations, finds real flights, explains what a place is actually like, and
builds a day-by-day itinerary you can export to your calendar.

It replies in whatever language you write in. Mostly Indonesian and English.

It is a portfolio piece, built by one developer, intended to be genuinely usable.
That shapes the design: it should look like a real product someone chose to build
well, not like a template with a chatbot bolted on.

## Who opens it

Two audiences, and the design has to serve both without splitting in two:

1. **A recruiter or engineer with 90 seconds.** They want to see it work and
   understand what was hard about building it. They will not sign up for anything.
2. **An actual traveller planning a trip.** They want the plan, not the tech.

The landing page carries audience 1. The chat carries audience 2. Both have to be
good.

---

## Screens

### 1. Landing (`/`)

#### Positioning — read this before designing anything on this page

This is **not** an OTA. It does not sell hotels, trains, cars, or attraction tickets,
and it should not pretend to. What it does is decide *what is worth booking* — which
place, which week, which flight, at which budget — and then hand off to whoever sells
it (`providers/booking_links.py` already does the handoff).

That makes the product **upstream of Traveloka, not a smaller copy of it.** Every
design decision on this page follows from that sentence. A tab bar with seven
verticals where four are dead would destroy the position in one glance; a page that
is only a chat box gives the position away by looking like a toy.

> **Amended in phase 4b.** "Upstream, not a copy" still holds and is still the
> whole position. What changed is where flight results live: a fixed-date flight
> search now navigates to `/flights` and renders a filterable list, because twenty
> flights compared by airline, time, and stops is genuinely a table, and a hero
> morphing into a table is a worse version of a page that can just exist. The rule
> below about the form not navigating survives everywhere else — flexible dates,
> inspiration, and free text all still answer in place. See
> [`phase-4-plan.md`](./phase-4-plan.md#the-results-page-amendment).

The three surfaces that are real, and therefore the only ones that get first-class
treatment:

| Surface | Backed by |
|---|---|
| Flights | `search_flights`, `search_flights_flexible` — Amadeus + Google Flights |
| Destinations & inspiration | `recommend_destinations`, `get_destination_info`, `search_knowledge` |
| Trip planning | the agent loop itself; itinerary lands in phase 5 |

#### The hero: a search bar that thinks

**The hero must contain a working agent, not a screenshot.** This is still the single
most important decision on the page. If the hero is a static image with a "Try it"
button, the page has failed.

But a bare chat input is a cold start. A visitor who does not know what to type sees
a blinking cursor and leaves. The fix is not to abandon the live agent — it is to give
it the affordance an OTA search widget has: **visible machinery, obvious inputs, zero
ambiguity about what the thing can do.**

So the hero is one module with a segmented control, three modes:

| Mode | Input | Fires |
|---|---|---|
| **Cari penerbangan** | From · To · Date(s) · Passengers | `search_flights` / `search_flights_flexible` |
| **Cari inspirasi** | Facet chips: budget band, trip style, region, season | `recommend_destinations` |
| **Tanya apa aja** | Free multiline text — the default | model decides |

All three submit to the same place. **The form does not navigate to a search results
page.** It seeds the agent with a structured tool call, and the hero morphs in place
into a streaming answer with `ToolActivity` visible — real tool, real prices, roughly
five seconds after landing. Then a "Lanjutkan di companion →" affordance carries the
session into `/chat`.

That is the whole trick, and it is worth stating plainly because it is what the design
has to protect: **the search form and the AI are the same engine.** A user who fills in
a form gets a conversation. A user who types a sentence gets the same tools. Neither
path is the "lesser" one.

Design consequences:

- The hero has to look composed in four states: empty, form-filled, streaming, and
  resolved-with-results. Resolved is the tallest — reserve for it, do not let the page
  jump when the answer arrives.
- Mode switching must not feel like three different products stapled together. Same
  container, same submit affordance, only the input region changes.
- The flight form is the densest thing on the page. It is also the most familiar, so
  it can carry more density than anything else without reading as cluttered.

#### Below the hero — the density layer

> **Amended after 4c.** The order below was wrong, and a real reader found it in one
> look: the fare rail came first, so the page showed prices to Bali before asking
> whether you wanted a beach at all. Someone without a destination cannot use a fare
> rail.
>
> The sections are now ordered by the question a visitor is actually holding, and each
> is numbered on screen so the sequence is visible rather than implied:
>
> | | Section | Answers |
> |---|---|---|
> | 01 | Inspiration | "no idea yet — where should I go?" |
> | 02 | Fare rail | "I know where — what does it cost from here?" |
> | 03 | Demo | "so what do I actually walk away with?" |
> | 04 | Positioning | "what do you get out of this?" |
>
> Two things below were **deleted rather than reordered**. The three capability cards
> described what the demo section now shows, and showing beats telling. The "cara
> kerjanya" stack table answered a question nobody planning a holiday has ever asked;
> it lives in the README, where an engineer will actually look for it.

This is what makes an OTA feel like a real product rather than a landing page:
**things to look at that are already answers.**

1. **`DealRail` — "Berangkat dari Jakarta"**
   A horizontal rail of real cheapest-fare cards to the curated destinations, origin
   auto-detected (`providers/geolocation.py`) with a manual override. Real prices, but
   **cached, not live** — see the constraint below. The single biggest "this is a real
   travel product" win available, and honest, because the numbers are true.

2. **`InspirationGrid` — "Mau liburan yang kayak gimana?"**
   Tiles built directly on the `TravelType` enum — beach, mountain, cultural, city,
   adventure, nature, foodie, shopping. Traveloka has a category row; the difference
   is that every tile here is a live `recommend_destinations` query, not a landing
   page for an SEO term.

3. **`BudgetBandPicker` — "Budget kamu berapa sehari?"**
   The four `BudgetCategory` bands as a row: under 500rb · 500rb–1jt · 1jt–2jt · di
   atas 2jt. Indonesian travellers lead with budget far more often than with
   destination, and no OTA lets them start there. This is a small component with an
   unfairly good conversion story — put it high, not buried.

4. **Three capability cards** — destination recommendations, real flight search,
   itinerary and calendar export.

5. **A preview of a trip board** (the shareable artefact).

6. **A short technical section** — stack, architecture, GitHub link. For audience 1.
   Confident, not boastful. It has more to say now: the seeded-tool-call architecture
   in the hero is the most interesting thing in the codebase.

#### Navigation

A top nav in the OTA idiom — but only the real verticals: Penerbangan · Inspirasi ·
Trip saya. No greyed-out tabs, no "coming soon" badges. An empty promise in the nav is
worse than a shorter nav.

Needs proper SEO and Open Graph treatment. It will be shared as a link.

### 2. Companion (`/chat`)

Two columns on desktop:

- **Left: the conversation.** Message thread, input, suggestion chips.
- **Right: the trip panel.** Fills in progressively as the conversation goes —
  destination, then dates, then flights, then itinerary. This panel is what makes it
  feel like a companion rather than a chatbot: the user watches their plan take
  shape instead of scrolling back through chat history to find what was decided.

The trip panel needs a considered empty state. It is empty for the first minute of
every session, so "empty" is a real state users see, not an edge case.

### 3. Trip board (`/trip/[id]`)

A saved trip at its own URL, shareable. Trip summary, chosen flights, itinerary by
day, calendar export button. Needs a dynamic Open Graph image — this is the thing
that gets pasted into a group chat.

### 4. Mobile

Chat goes full-screen. The trip panel becomes a bottom sheet with a peek state
showing how far along the plan is. The panel must remain discoverable — if it is
buried behind a button, the companion feeling is lost on mobile, which is where most
Indonesian users will be.

---

## Components

### Landing surface

| Component | Notes |
|---|---|
| `SearchCommandBar` | The hero. Segmented control over three modes, one shared submit. Owns the empty → filled → streaming → resolved transition, so it must not be three components in a trench coat. |
| `FlightSearchForm` | From · To · Date(s) · Passengers. Origin/destination are city names or IATA — `lookup_place` resolves either, so the field can stay forgiving. A "tanggal fleksibel" toggle switches the submit from `search_flights` to `search_flights_flexible`. |
| `ExploreFacets` | Chips for budget band, trip style (multi-select), region, season. Every filter is optional — the tool takes no required arguments, and the UI should make that feel deliberate rather than unfinished. |
| `BudgetBandPicker` | Four bands from `BudgetCategory`. Also reused inside `ExploreFacets`. IDR ranges, so the money treatment applies. |
| `OriginPicker` | Auto-detected city with a visible, one-tap override. Detection is a guess and must be styled as a guess, never as a fact the user has to fight. |
| `HeroLiveAnswer` | The morphed hero: streaming text, one or more `ToolActivity` rows, result cards, and the hand-off to `/chat`. Reuses `ChatBubble` and the result cards rather than reimplementing them. |
| `DealRail` / `DealCard` | Snap-scrolling fare rail. Card carries destination, cheapest price in IDR, and a **staleness timestamp** — the prices are cached, and the card has to say so without undermining trust in them. |
| `InspirationGrid` / `InspirationTile` | Eight `TravelType` tiles. Tile labels in Indonesian run long ("petualangan", "kuliner") — do not design to the width of "beach". |
| `SiteNav` | Penerbangan · Inspirasi · Trip saya. Collapses to the command bar's mode switcher on mobile rather than duplicating it. |

### Core chat

| Component | Notes |
|---|---|
| `ChatBubble` | Variants: user, agent, **tool-running**, **error**. Agent messages render Markdown — headings, bold, ordered lists, tables. Answers are frequently long and structured. |
| `ChatInput` | Multiline, grows with content, submit on Enter. |
| `SuggestionChips` | 3–4 follow-up prompts under the latest agent message. Text is user-generated and varies in length; they must wrap gracefully. |
| `TypingIndicator` | Shown between sending and the first token. |

### Tool activity — needs real design attention

The agent calls tools and the UI is told about it in two stages: `tool_start` (with
the arguments) and `tool_result` (with the data). This is the most distinctive part
of the product and the easiest to get wrong.

Design a `ToolActivity` element that shows what the agent is doing in plain language
— "searching flights Jakarta → Bali", "looking up Yogyakarta", "reading travel
guides" — and then resolves into either a result or a failure. Several tools can run
at once, so more than one may be active simultaneously.

The tension to solve: it should feel like transparency, not like a debug console. A
user who does not care about the mechanics should still find it reassuring. A user
who does care should be able to see exactly what happened.

Tools that exist today: `lookup_place`, `resolve_dates`, `search_flights`,
`search_flights_flexible`, `recommend_destinations`, `get_destination_info`,
`search_knowledge`.

### Result cards

| Component | Content |
|---|---|
| `FlightCard` | Airline, departure/arrival times, duration, stops, price in IDR. Cheapest option needs distinction. Booking link out to a third party. |
| `DestinationCard` | Name, country, one-line description, daily cost in IDR, trip-style tags, best season, highlights. |
| `ItineraryDayCard` | A day: time-ordered activities, each with location and cost estimate. |
| `KnowledgePassage` | A quoted passage from the travel guide corpus, with attribution and a link. Must read as a citation, clearly distinct from the agent's own words. |

### Trip panel

| Component | Notes |
|---|---|
| `TripPanel` | Container. Sections appear as they are filled: destination → dates → flights → itinerary. Needs a strong empty state. |
| `TripProgress` | How complete the plan is. Drives the mobile bottom-sheet peek. |
| `CalendarExportButton` | Downloads a `.ics` file. Needs a brief explanation of what happens next — users do not know what a `.ics` is. |

### Access — bring your own key

| Component | Notes |
|---|---|
| `QuotaBanner` | "N free messages left today." Unobtrusive at 5 remaining, harder to ignore at 1, becomes a wall at 0. |
| `ApiKeyDialog` | Where a user pastes their own API key to remove the limit. |

`ApiKeyDialog` carries a trust problem worth designing for rather than papering
over. You are asking someone to paste a credential into a website. The dialog has to
state plainly that the key is never stored, never logged, and goes only to their
chosen provider — and it has to *look* like something trustworthy, because the
copy alone will not carry it. Provider choice (Gemini / OpenAI / Anthropic) belongs
here too. Assume a user who is cautious and slightly suspicious. That is the correct
posture and the design should reward it.

---

## Design tokens

Deliver tokens as **CSS custom properties ready to paste into Tailwind v4's
`@theme` block**. This project uses Tailwind v4 with config-in-CSS — there is no
`tailwind.config.js` and JS-object theme config cannot be used.

```css
@theme {
  --color-brand-500: oklch(...);
  --radius-card: ...;
  ...
}
```

Needed:
- Full colour scale, light and dark, both first-class
- Semantic colours: success, warning, error, and something for "price" — money
  appears constantly and deserves consistent treatment
- Type scale — long Markdown answers need a comfortable reading rhythm
- Radius, shadow, spacing scales
- Motion: durations and easings. Streaming text and appearing tool status both need
  motion that feels alive without being distracting.

---

## Constraints that come from the implementation

These are not preferences. They come from how the thing actually works.

1. **Indonesian text runs roughly 15–20% longer than English** for the same meaning.
   Buttons, chips, and labels need slack. "Cari penerbangan" vs "Find flights".
2. **The agent streams.** Text arrives token by token. Layout must not jump as it
   grows, and the container cannot rely on knowing its final height.
3. **Tool activity is interleaved with text.** The agent may write a sentence, call a
   tool, then continue writing. A message is not a single atomic block.
4. **Tools fail, and the agent says so honestly.** It is designed never to invent a
   price when a lookup fails. Failure states are a normal part of the experience and
   deserve real design, not a red toast.
5. **Existing components follow shadcn/ui conventions** — `button`, `card`,
   `avatar`, `scroll-area`, `textarea` already exist and will be extended.
6. **Prices are IDR**, frequently in the hundreds of thousands to millions. Long
   numbers. `Rp 1.250.000` needs to stay readable in a card.
7. **Dark mode is not optional.** Assume roughly half the audience for a developer
   portfolio views in dark.
8. **The curated destination set is 15 places** — Yogyakarta, Lombok, Belitung,
   Bandung, Malang, Kuala Lumpur, Ho Chi Minh City, Chiang Mai, Siem Reap, Penang,
   Vientiane, Tokyo, Osaka, Kyoto, Fukuoka. Indonesia, Southeast Asia, Japan. Rails
   and grids must look intentional at that size, not like a grid waiting to be
   filled. Fifteen well-chosen places reads as curation; fifteen in a layout built
   for two hundred reads as an empty database.
9. **Landing-page prices are cached, not live.** A live rail would cost 15
   destinations × up to 7 provider calls per page view. Deals are served from a
   warmed cache with a visible "diperbarui N jam lalu". Design the staleness marker
   as a normal, confident part of the card — hiding it is the only way this becomes
   dishonest.
10. **A form submission and a typed sentence enter the agent through the same door.**
    The hero's structured modes seed a validated tool call; they do not bypass the
    conversation. So every result the hero can show is a result the chat can also
    show, and the components are shared rather than parallel.

---

## Tone

Warm and competent. The agent's own voice is relaxed Indonesian that mixes in
English loanwords naturally — the design should sit alongside that, not fight it
with corporate travel-brand polish.

Reference points worth stealing from: Linear's density and restraint, Perplexity's
handling of streaming answers and citations, Raycast's confidence in dark mode. Not
travel-agency aesthetics — no stock photos of beaches, no wanderlust script fonts.
The product's value is judgement and real data, and it should look like it.

> **Amended after 4c.** The first build followed this section too literally and came out
> correct but cold: one blue ramp, two animations, nothing to look at. The rule was
> never "no colour" — it was "no decoration pretending to be function". Those are
> different, and the page needed the second without the first.
>
> What the palette is now, and the boundary that keeps it from becoming an OTA:
>
> - **Two ramps.** Brand (ocean, hue 236) and warm (terracotta, hue 32). Two
>   complementary hues read as a decision; a scattering reads as indecision. The warm
>   one is deliberately clear of `--color-warning` so an accent is never mistaken for
>   an alarm.
> - **Eight category hues**, one per `TravelType`, all at *identical* lightness and
>   chroma — only hue moves. That is what makes eight colours a family rather than a
>   pile of stickers, and it is honest: no travel type outranks another, so none of
>   them should look louder.
> - **Illustration is geometry, drawn here, in `components/illustration/`.** Still no
>   photographs and no mascots. Every stroke uses a token, so dark mode needs no second
>   asset.
> - **Motion is entrance and atmosphere only** — sections arriving as you scroll, a
>   six-pixel drift on one illustration. Nothing loops in the corner of the eye, and
>   every path honours `prefers-reduced-motion`.
>
> Anything beyond those four needs a reason that is not taste. The target is still
> "Linear built a travel product for Indonesia", just with the warmth that description
> always implied.

> **Amended after 4e.** The 4c amendment above was written and then largely not
> delivered, and the gap was invisible because nothing failed. Three corrections.
>
> **The typeface was never loading.** `globals.css` named `"Inter"` and
> `"JetBrains Mono"` for months, and nothing anywhere fetched either — no
> `next/font`, no `@font-face`, no link tag. Every visitor read this site in their
> OS UI font, and the prices this brief sets in mono with tabular figures fell back
> to a generic monospace. A type system that is only a CSS variable is decoration.
> It is **Plus Jakarta Sans** now, self-hosted through `next/font`, chosen over
> restoring Inter for two reasons: Inter is the most recognisable signature of a
> generated interface, and a humanist sans commissioned for Jakarta carries
> Indonesian better than Inter's mechanical evenness.
>
> **"Motion is entrance and atmosphere only" was too narrow.** It produced a page
> that arrived and then died — hover states everywhere and no acknowledgement of a
> click anywhere on the site. The rule is now *motion must be caused*: either the
> reader caused it (press, hover, scroll) or it happens once on arrival. What is
> still banned is the thing that rule was written against — anything looping in the
> corner of the eye, and anything that moves while you are reading it. The demo
> section is the test case: it used to advance itself every 3.8 seconds and now the
> step is a function of scroll position, so it only ever moves because someone
> asked, and it runs backwards too.
>
> **The logo was a Lucide compass in a rounded square** — the mark every generated
> product ships with, and the wrong idea besides, since a compass points at a
> direction and this product is about the leg between two named places. The mark is
> now that arc, the same drawing as the hero illustration rather than unrelated art,
> origin in brand and arrival in warm.
>
> The four palette rules above stand unchanged.
>
> **A fifth rule, learned the hard way: an empty state must carry information,
> not report its own emptiness.** The fare rail with a cold cache rendered eight
> identical cards reading "harga belum tersimpan", and a reader looking at it
> could not tell what the section was even for. The fare is genuinely unknown
> until someone asks — but the fare was never the only real thing available. The
> catalogue already knows each destination's daily cost, what kind of trip it is,
> and why it is worth going, none of which needs a provider call. The cold state
> now shows more than the warm one would, not less.
>
> This is also where the eight category hues finally earn their place: they were
> designed in 4c and then used on exactly one screen. A destination that says what
> kind of trip it is, in the colour that kind wears everywhere else, is doing the
> work the palette was built for.

One borrowed thing, deliberately: **the information density of an Indonesian OTA
homepage.** Traveloka's landing page is busy, and that busyness is not a mistake —
it signals capability to a user who is about to spend two million rupiah. Take the
density and the structured-search affordance. Leave the gradients, the mascot
illustrations, the promo confetti, and the seven-vertical tab bar.

The target is what you would get if Linear built a travel product for Indonesia: dense
but calm, every element load-bearing, nothing decorative pretending to be functional.

---

## What to deliver

1. The four screens above, desktop and mobile
2. The component set, with states: default, loading, error, empty
3. Tokens as CSS custom properties for `@theme`
4. Specific attention to `ToolActivity` and `ApiKeyDialog` — these are the two
   pieces with no obvious precedent to copy
5. The `SearchCommandBar` in all four of its states, and the transition between them.
   This is the piece the whole landing page rests on: it has to read as a capable
   search widget before it is used and as a live agent after. Getting only one of
   those right is the most likely way this design fails.

Implementation sequencing, the backend changes the hero requires, and the risks that
come with them are in [`phase-4-plan.md`](./phase-4-plan.md).
