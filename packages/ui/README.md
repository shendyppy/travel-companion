# @travel/ui

Shared design system. **Not populated yet** — waiting on Claude Design output
(phase 4).

Planned contents:

- Tokens as CSS custom properties, ready to drop into Tailwind v4's `@theme`
  (this project uses Tailwind v4, config-in-CSS, not `tailwind.config.js`)
- Shared shadcn/ui primitives: `button`, `card`, `avatar`, `scroll-area`, `textarea`
- Domain components: `ChatBubble`, `FlightCard`, `DestinationCard`,
  `ItineraryDayCard`, `TripPanel`, `SuggestionChips`, `TypingIndicator`,
  `CalendarExportButton`, `ApiKeyDialog`, `QuotaBanner`

For now the salvaged components still live in `apps/web/src/components/`. They move
here in phase 4, once it is clear which ones are genuinely used across more than one
page (landing, chat, trip board) — no point promoting something that turns out to be
used once.
