# @travel/ui

Design system bersama. **Belum diisi** — nunggu output Claude Design (Fase 2).

Rencananya berisi:

- Token dalam bentuk CSS custom property yang siap tempel ke `@theme` Tailwind v4
  (project ini pakai Tailwind v4, config-in-CSS, bukan `tailwind.config.js`)
- Primitif shadcn/ui bersama: `button`, `card`, `avatar`, `scroll-area`, `textarea`
- Komponen domain: `ChatBubble`, `FlightCard`, `DestinationCard`, `ItineraryDayCard`,
  `TripPanel`, `SuggestionChips`, `TypingIndicator`, `CalendarExportButton`

Sementara ini komponen hasil salinan masih nongkrong di `apps/web/src/components/`.
Dipindah ke sini pas Fase 2, setelah ketahuan mana yang beneran kepakai lintas halaman
(landing, chat, trip board) — biar nggak kepagian mindahin yang ternyata cuma dipakai sekali.
