"use client";

/**
 * The last thing on the page: the positioning, said out loud.
 *
 * This file used to also hold three capability cards and a "cara kerjanya"
 * section with a stack table. Both are gone. The cards described what
 * `DemoSection` now shows, and showing beats telling; the stack table answered a
 * question no one planning a holiday has ever asked, and it belongs in the
 * README where an engineer will actually go looking for it.
 *
 * What survives is the one paragraph that cannot live anywhere else: why there
 * are no hotels. Someone always asks, and "belum sempat" is the wrong answer.
 */

import Link from "next/link";
import { GithubMark } from "@/components/ui/GithubMark";
import { useInView } from "@/hooks/useInView";
import { useMessages } from "@/components/i18n/MessagesProvider";

export function BelowFold() {
  const { ref, props } = useInView<HTMLElement>();
  const { m, locale } = useMessages();

  return (
    <>
      <section ref={ref} {...props} className="reveal border-t border-border py-16">
        <div className="mx-auto max-w-3xl px-5">
          <p className="tabular mb-1.5 font-mono text-2xs font-medium uppercase tracking-widest text-warm">
            {m.trust.eyebrow}
          </p>
          <h2 className="text-balance text-2xl font-semibold tracking-tight">{m.trust.title}</h2>
          <p className="mt-4 text-pretty text-base text-fg-muted">
            {m.trust.body1Before}
            <strong className="font-medium text-fg">{m.trust.body1Strong}</strong>
            {m.trust.body1After}
          </p>
          <p className="mt-3 text-pretty text-base text-fg-muted">{m.trust.body2}</p>
        </div>
      </section>

      <footer className="border-t border-border py-10">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5">
          <p className="text-sm text-fg-subtle">{m.footer.note}</p>
          <div className="flex items-center gap-4">
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
        </div>
      </footer>
    </>
  );
}
