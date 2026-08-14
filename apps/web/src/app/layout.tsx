import type { Metadata, Viewport } from "next";
import "./globals.css";

const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

/**
 * This page gets pasted into group chats and shared with recruiters, so the
 * Open Graph treatment is part of the product rather than an afterthought.
 */
export const metadata: Metadata = {
  metadataBase: new URL(SITE),
  title: {
    default: "Travel Companion — rencanain perjalanan, bukan cuma cari tiket",
    template: "%s · Travel Companion",
  },
  description:
    "AI travel companion buat traveller Indonesia. Ceritain budget dan vibe-nya, dia cariin destinasi, ngecek harga penerbangan beneran, terus nyusun itinerary-nya.",
  keywords: ["travel", "penerbangan", "itinerary", "AI", "Indonesia", "liburan"],
  authors: [{ name: "Shendy Putra Perdana Yohansah" }],
  openGraph: {
    type: "website",
    locale: "id_ID",
    url: SITE,
    siteName: "Travel Companion",
    title: "Rencanain perjalanan, bukan cuma cari tiket",
    description:
      "Ceritain budget dan vibe-nya. Dia cariin destinasi, ngecek harga penerbangan beneran, terus nyusun itinerary-nya.",
  },
  twitter: {
    card: "summary_large_image",
    title: "Travel Companion",
    description: "AI travel companion buat traveller Indonesia.",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fafbfc" },
    { media: "(prefers-color-scheme: dark)", color: "#0e1116" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id" suppressHydrationWarning>
      <head>
        {/*
          Dark mode is resolved before first paint. Doing it in React would mean
          a flash of the light theme on every load for roughly half the audience
          — a developer portfolio skews dark, and the brief treats dark as
          first-class rather than as a toggle.
        */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var s=localStorage.getItem('tc:theme');var d=s?s==='dark':matchMedia('(prefers-color-scheme:dark)').matches;if(d)document.documentElement.classList.add('dark')}catch(e){}})()`,
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
