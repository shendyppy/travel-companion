import type { Metadata, Viewport } from "next";
import { notFound } from "next/navigation";
import "../globals.css";
import { DEFAULT_LOCALE, LOCALES, getMessages, isLocale, type Locale } from "@/lib/i18n";
import { MessagesProvider } from "@/components/i18n/MessagesProvider";

const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

/**
 * The root layout, and it lives under `[locale]` on purpose: `<html lang>` has
 * to say which language the page is in, and that is not knowable above this
 * segment. Screen readers switch pronunciation on it and translation tools key
 * off it, so getting it wrong is worse than not setting it.
 */
export function generateStaticParams() {
  return LOCALES.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const m = getMessages(locale);
  const active: Locale = isLocale(locale) ? locale : DEFAULT_LOCALE;

  return {
    metadataBase: new URL(SITE),
    title: { default: m.meta.title, template: "%s · Travel Companion" },
    description: m.meta.description,
    authors: [{ name: "Shendy Putra Perdana Yohansah" }],
    alternates: {
      canonical: `/${active}`,
      // Both languages point at each other so a search engine indexes them as
      // one page in two languages rather than as duplicates competing with
      // themselves. x-default sends anyone unmatched to Indonesian, which is who
      // this is built for.
      languages: {
        id: "/id",
        en: "/en",
        "x-default": `/${DEFAULT_LOCALE}`,
      },
    },
    openGraph: {
      type: "website",
      locale: active === "id" ? "id_ID" : "en_US",
      alternateLocale: active === "id" ? "en_US" : "id_ID",
      url: `${SITE}/${active}`,
      siteName: "Travel Companion",
      title: m.meta.ogTitle,
      description: m.meta.ogDescription,
    },
    twitter: {
      card: "summary_large_image",
      title: m.meta.ogTitle,
      description: m.meta.ogDescription,
    },
    robots: { index: true, follow: true },
  };
}

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fafbfc" },
    { media: "(prefers-color-scheme: dark)", color: "#0e1116" },
  ],
};

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  // The middleware only ever writes a valid locale, so anything else here was
  // typed by hand or guessed by a crawler. A 404 is the honest answer; falling
  // back to Indonesian would leave /fr silently serving a page that claims to be
  // French in its own URL.
  if (!isLocale(locale)) notFound();

  const messages = getMessages(locale);

  return (
    <html lang={locale} suppressHydrationWarning>
      <head>
        {/*
          Dark mode is resolved before first paint. Doing it in React would mean
          a flash of the light theme on every load for roughly half the audience
          — a developer portfolio skews dark, and dark is first-class here rather
          than a toggle.
        */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var s=localStorage.getItem('tc:theme');var d=s?s==='dark':matchMedia('(prefers-color-scheme:dark)').matches;if(d)document.documentElement.classList.add('dark')}catch(e){}})()`,
          }}
        />
      </head>
      <body>
        <MessagesProvider locale={locale} messages={messages}>
          {children}
        </MessagesProvider>
      </body>
    </html>
  );
}
