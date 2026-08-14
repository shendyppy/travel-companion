import Link from "next/link";
import { Compass } from "lucide-react";
import { GithubMark } from "@/components/ui/GithubMark";

/**
 * Top navigation.
 *
 * Three entries, all of which work. There is no Hotels, no Trains, no Cars, and
 * no greyed-out "coming soon" — an empty promise in the nav is worse than a
 * shorter nav, and this product is upstream of the OTA rather than a smaller
 * copy of one.
 */
export function SiteNav() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-bg/85 backdrop-blur">
      <nav className="mx-auto flex h-14 max-w-6xl items-center gap-6 px-5">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
          <span className="grid size-7 place-items-center rounded-md bg-accent" aria-hidden>
            <Compass className="size-4 text-accent-fg" />
          </span>
          Travel Companion
        </Link>

        <div className="ml-auto flex items-center gap-1 text-sm">
          <Link
            href="/#penerbangan"
            className="rounded-lg px-3 py-1.5 text-fg-muted transition-colors hover:bg-surface-2 hover:text-fg"
          >
            Penerbangan
          </Link>
          <Link
            href="/#inspirasi"
            className="rounded-lg px-3 py-1.5 text-fg-muted transition-colors hover:bg-surface-2 hover:text-fg"
          >
            Inspirasi
          </Link>
          <Link
            href="/chat"
            className="rounded-lg px-3 py-1.5 font-medium text-accent transition-colors hover:bg-accent-soft"
          >
            Companion
          </Link>
          <a
            href="https://github.com/shendyppy"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="GitHub"
            className="ml-1 grid size-9 place-items-center rounded-lg text-fg-muted transition-colors hover:bg-surface-2 hover:text-fg"
          >
            <GithubMark className="size-4" />
          </a>
        </div>
      </nav>
    </header>
  );
}
