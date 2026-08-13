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

**The hero must contain a working chat, not a screenshot.** This is the single most
important decision in the whole design. A visitor types one sentence and watches the
agent think, call a tool, and answer. If the hero is a static image with a "Try it"
button, the page has failed — it becomes indistinguishable from every other AI
landing page.

So the hero needs to accommodate: an input, a stream of response text arriving
progressively, and a tool-status line that appears and disappears. It should look
composed while empty and while full.

Below the hero:
- Three capability cards: destination recommendations, real flight search, itinerary
  and calendar export
- A preview of a trip board (the shareable artefact)
- A short technical section — stack, architecture, GitHub link. This is for audience
  1 and should read as confident, not boastful.

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

---

## Tone

Warm and competent. The agent's own voice is relaxed Indonesian that mixes in
English loanwords naturally — the design should sit alongside that, not fight it
with corporate travel-brand polish.

Reference points worth stealing from: Linear's density and restraint, Perplexity's
handling of streaming answers and citations, Raycast's confidence in dark mode. Not
travel-agency aesthetics — no stock photos of beaches, no wanderlust script fonts.
The product's value is judgement and real data, and it should look like it.

---

## What to deliver

1. The four screens above, desktop and mobile
2. The component set, with states: default, loading, error, empty
3. Tokens as CSS custom properties for `@theme`
4. Specific attention to `ToolActivity` and `ApiKeyDialog` — these are the two
   pieces with no obvious precedent to copy
