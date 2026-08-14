/**
 * Everything under the density layer: what it does, what it produces, and how it
 * was built.
 *
 * This is the half of the page that serves the recruiter rather than the
 * traveller. The brief's rule for it — confident, not boastful — is easier to
 * keep by being specific: "6.000 bandara" and "76 tes" say more than "robust"
 * and "production-grade", and they are checkable.
 */

import { CalendarDays, MapPinned, Plane } from "lucide-react";
import { GithubMark } from "@/components/ui/GithubMark";

const CAPABILITIES = [
  {
    icon: MapPinned,
    title: "Rekomendasi destinasi",
    body: "Lima belas destinasi kurasi dengan biaya harian dalam rupiah — angka yang biasanya dikarang model kalau dibiarkan sendiri.",
  },
  {
    icon: Plane,
    title: "Harga penerbangan beneran",
    body: "Amadeus dan Google Flights, bukan estimasi. Kalau lookup-nya gagal, dia bilang gagal — bukan ngarang harga.",
  },
  {
    icon: CalendarDays,
    title: "Itinerary siap ekspor",
    body: "Rencana per hari yang bisa langsung masuk kalender kamu sebagai .ics.",
  },
];

const STACK = [
  ["Web", "Next.js App Router · TypeScript · Tailwind v4"],
  ["API", "FastAPI · Python 3.13 · LiteLLM · Redis"],
  ["Model", "Provider-agnostic — Gemini, OpenAI, Anthropic, GLM"],
  ["Data penerbangan", "Amadeus + Google Flights"],
  ["Knowledge base", "ChromaDB · embedding ONNX in-process"],
];

export function BelowFold() {
  return (
    <>
      <section className="border-t border-border py-12">
        <div className="mx-auto max-w-6xl px-5">
          <h2 className="text-xl font-semibold tracking-tight">Yang dia kerjain</h2>
          <ul className="mt-5 grid gap-3 sm:grid-cols-3">
            {CAPABILITIES.map(({ icon: Icon, title, body }) => (
              <li key={title} className="rounded-card border border-border bg-surface p-5">
                <span className="grid size-9 place-items-center rounded-lg bg-accent-soft" aria-hidden>
                  <Icon className="size-4.5 text-accent" />
                </span>
                <h3 className="mt-3 font-medium">{title}</h3>
                <p className="mt-1.5 text-sm text-fg-muted">{body}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* The positioning, said out loud. Someone will ask why there are no
          hotels, and "belum sempat" is the wrong answer. */}
      <section className="border-t border-border py-12">
        <div className="mx-auto max-w-3xl px-5">
          <h2 className="text-xl font-semibold tracking-tight">Kenapa nggak jualan hotel?</h2>
          <p className="mt-3 text-pretty text-base text-fg-muted">
            Karena mesin rekomendasi yang juga ambil komisi booking punya konflik kepentingan,
            dan yang ini nggak. Tugasnya mutusin{" "}
            <strong className="font-medium text-fg">apa yang layak dibeli</strong> — kota mana,
            minggu keberapa, penerbangan yang mana — terus nyerahin ke yang jualan. Dia berdiri
            di hulu OTA, bukan jadi versi kecilnya.
          </p>
        </div>
      </section>

      <section className="border-t border-border py-12">
        <div className="mx-auto max-w-6xl px-5">
          <h2 className="text-xl font-semibold tracking-tight">Cara kerjanya</h2>
          <p className="mt-3 max-w-2xl text-pretty text-base text-fg-muted">
            Agent-nya loop tool-calling. Nggak ada deteksi intent pakai regex di mana pun — model
            yang mutusin user mau apa lewat pilihan tool-nya. Form pencarian di atas nggak lewat
            jalur lain: dia ngirim tool call tervalidasi bareng pesannya, dan hasilnya masuk ke
            percakapan yang sama.
          </p>

          <dl className="mt-6 grid gap-x-8 gap-y-3 sm:grid-cols-2">
            {STACK.map(([label, value]) => (
              <div key={label} className="flex flex-wrap gap-x-3 border-b border-border py-2.5">
                <dt className="w-36 shrink-0 text-sm text-fg-subtle">{label}</dt>
                <dd className="text-sm">{value}</dd>
              </div>
            ))}
          </dl>

          <a
            href="https://github.com/shendyppy"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-6 inline-flex h-10 items-center gap-2 rounded-lg border border-border-strong px-5 text-sm font-medium transition-colors hover:bg-surface-2"
          >
            <GithubMark className="size-4" />
            Lihat kodenya
          </a>
        </div>
      </section>

      <footer className="border-t border-border py-8">
        <div className="mx-auto max-w-6xl px-5 text-sm text-fg-subtle">
          Dibikin sama satu orang. Harga penerbangan dari penyedia pihak ketiga dan bisa berubah.
        </div>
      </footer>
    </>
  );
}
