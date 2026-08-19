"use client";

/**
 * The end of the page.
 *
 * This was a full section arguing the positioning — why there are no hotels —
 * and it was cut down to a footnote after a reader said, fairly, that it had no
 * point where it stood. The argument is still worth making: someone always asks,
 * and "belum sempat" is the wrong answer. But it is a footnote's worth of
 * argument, not a screen's, and giving it a whole band of the page implied the
 * visitor came here to read about product strategy.
 *
 * So it sits above the footer links now, at footnote size, where the people who
 * actually want it — the ones who read to the bottom — will find it.
 */

import Link from "next/link";
import { GithubMark } from "@/components/ui/GithubMark";
import { Mark } from "@/components/illustration/Mark";
import { useInView } from "@/hooks/useInView";
import { useMessages } from "@/components/i18n/MessagesProvider";

export function BelowFold() {
  const { ref, props } = useInView<HTMLElement>();
  const { m, locale } = useMessages();

  return (
    <footer ref={ref} {...props} className="reveal border-t border-border">
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-14 lg:grid-cols-[1.4fr_1fr] lg:gap-16">
        <div className="max-w-2xl">
          <p className="eyebrow mb-2 font-mono text-2xs font-semibold text-warm">
            {m.trust.eyebrow}
          </p>
          <h2 className="display text-xl sm:text-2xl">{m.trust.title}</h2>
          <p className="mt-3 text-pretty text-sm leading-relaxed text-fg-muted">
            {m.trust.body1Before}
            <strong className="font-medium text-fg">{m.trust.body1Strong}</strong>
            {m.trust.body1After}
          </p>
          <p className="mt-2.5 text-pretty text-sm leading-relaxed text-fg-muted">{m.trust.body2}</p>
        </div>

        <div className="flex flex-col gap-4 lg:items-end lg:text-right">
          <p className="flex items-center gap-2 font-semibold tracking-[--tracking-heading] lg:flex-row-reverse">
            <Mark className="size-6 shrink-0 text-accent" />
            Travel Companion
          </p>

          <div className="flex flex-wrap items-center gap-4">
            <Link
              href={`/${locale}/chat`}
              className="text-sm font-medium text-accent hover:underline"
            >
              {m.footer.openCompanion}
            </Link>
            <a
              href="https://github.com/shendyppy"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm font-medium text-fg-muted hover:text-fg"
            >
              <GithubMark className="size-4" />
              {m.footer.code}
            </a>
          </div>

          <p className="text-xs text-fg-subtle">{m.footer.note}</p>
        </div>
      </div>
    </footer>
  );
}
