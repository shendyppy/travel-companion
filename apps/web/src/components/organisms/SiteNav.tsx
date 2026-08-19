"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { GithubMark } from "@/components/ui/GithubMark";
import { Wordmark } from "@/components/illustration/Mark";
import { useMessages } from "@/components/i18n/MessagesProvider";
import { useScrolled } from "@/hooks/useScrolled";
import { LOCALES, localePath, type Locale } from "@/lib/i18n";

/**
 * Top navigation.
 *
 * Three entries, all of which work. There is no Hotels, no Trains, no Cars, and
 * no greyed-out "coming soon" — an empty promise in the nav is worse than a
 * shorter nav, and this product is upstream of the OTA rather than a smaller
 * copy of one.
 */
export function SiteNav() {
  const { m, locale } = useMessages();
  const scrolled = useScrolled();
  const base = `/${locale}`;

  return (
    // At rest the header is part of the hero: no border, no blur, nothing
    // separating it from the page. The divider appears only once there is
    // something scrolled underneath it, which is the only moment it means
    // anything.
    <header
      className={cn(
        "sticky top-0 z-40 transition-[background-color,border-color,box-shadow] duration-[--duration-normal]",
        scrolled
          ? "border-b border-border bg-bg/85 shadow-card backdrop-blur"
          : "border-b border-transparent bg-transparent",
      )}
    >
      <nav className="mx-auto flex h-14 max-w-6xl items-center gap-4 px-5">
        <Link href={base} aria-label="Travel Companion">
          <Wordmark className="flex items-center gap-2" animated />
        </Link>

        <div className="ml-auto flex items-center gap-1 text-sm">
          <Link
            href={`${base}#penerbangan`}
            className="hidden rounded-lg px-3 py-1.5 text-fg-muted transition-colors hover:bg-surface-2 hover:text-fg sm:block"
          >
            {m.nav.flights}
          </Link>
          <Link
            href={`${base}#inspirasi`}
            className="hidden rounded-lg px-3 py-1.5 text-fg-muted transition-colors hover:bg-surface-2 hover:text-fg sm:block"
          >
            {m.nav.inspiration}
          </Link>
          <Link
            href={`${base}/chat`}
            data-tour="companion"
            className="rounded-lg px-3 py-1.5 font-medium text-accent transition-colors hover:bg-accent-soft"
          >
            {m.nav.companion}
          </Link>

          <LocaleSwitch current={locale} />

          <a
            href="https://github.com/shendyppy"
            target="_blank"
            rel="noopener noreferrer"
            aria-label={m.nav.github}
            className="grid size-9 place-items-center rounded-lg text-fg-muted transition-colors hover:bg-surface-2 hover:text-fg"
          >
            <GithubMark className="size-4" />
          </a>
        </div>
      </nav>
    </header>
  );
}

/**
 * Two links rather than a dropdown.
 *
 * With exactly two options a dropdown costs a click to reveal what a pair of
 * two-letter labels can just show. They are real links, so the other language is
 * crawlable and a middle-click opens it in a tab.
 *
 * The cookie is written on click so a later visit to a bare path lands on the
 * language the reader actually chose, rather than on whatever their browser
 * happens to advertise. The URL still wins over the cookie — see `middleware.ts`.
 */
function LocaleSwitch({ current }: { current: Locale }) {
  const pathname = usePathname();
  const { m } = useMessages();

  return (
    <div
      className="ml-1 flex items-center rounded-lg border border-border p-0.5"
      role="group"
      aria-label={m.nav.language}
    >
      {LOCALES.map((locale) => (
        <Link
          key={locale}
          href={localePath(pathname, locale)}
          hrefLang={locale}
          aria-current={locale === current ? "true" : undefined}
          onClick={() => {
            document.cookie = `tc:locale=${locale}; path=/; max-age=31536000; samesite=lax`;
          }}
          className={cn(
            "rounded-md px-2 py-1 text-xs font-medium uppercase transition-colors",
            locale === current
              ? "bg-accent-soft text-accent"
              : "text-fg-subtle hover:bg-surface-2 hover:text-fg",
          )}
        >
          {locale}
        </Link>
      ))}
    </div>
  );
}
