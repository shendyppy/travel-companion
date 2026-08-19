import { ImageResponse } from "next/og";
import { getMessages } from "@/lib/i18n";

/**
 * The card that shows up when this link is pasted anywhere.
 *
 * Worth building properly rather than shipping a screenshot: a link to this page
 * gets sent to a recruiter or dropped in a group chat far more often than it
 * gets typed, so for most people this image *is* the first impression.
 *
 * Generated per locale, because the tagline is the one line doing the work and
 * an Indonesian tagline under an English page is a small, avoidable confusion.
 *
 * Deliberately no illustration and no photograph. Satori supports a subset of
 * CSS, complex SVG renders unpredictably in it, and a card that is type and one
 * accent rule is both safer and closer to how the product actually looks.
 */

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "Travel Companion";

export default async function OpengraphImage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const m = getMessages(locale);

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          // Hard-coded rather than read from the token file: this renders on the
          // server with no CSS pipeline, so a custom property would come out as
          // the literal string.
          background: "#0e1116",
          color: "#f2f5f8",
          padding: "72px 80px",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 10,
              background: "#3b93d4",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 26,
            }}
          >
            ✈
          </div>
          <div style={{ fontSize: 26, fontWeight: 600, letterSpacing: -0.4 }}>
            Travel Companion
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div
            style={{
              fontSize: 68,
              fontWeight: 700,
              letterSpacing: -2,
              lineHeight: 1.08,
              maxWidth: 940,
            }}
          >
            {m.meta.ogTitle}
          </div>
          <div style={{ fontSize: 28, color: "#9aa7b4", lineHeight: 1.4, maxWidth: 880 }}>
            {m.meta.ogDescription}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 14, fontSize: 22 }}>
          <div style={{ width: 56, height: 4, borderRadius: 999, background: "#e0794f" }} />
          {/* One interpolated string, not text plus an expression. Satori treats
              those as two child nodes and refuses to lay out a div with more
              than one child unless it declares a display mode. */}
          <div style={{ color: "#9aa7b4" }}>
            {`Amadeus · Google Flights · ${locale.toUpperCase()}`}
          </div>
        </div>
      </div>
    ),
    size,
  );
}
