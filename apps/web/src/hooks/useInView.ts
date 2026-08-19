"use client";

/**
 * Tells an element when it has been scrolled to.
 *
 * Pairs with the `reveal` utility in `globals.css`: that class holds a section
 * at opacity 0 and this flips `data-inview`, letting CSS do the animating. No
 * animation library, no scroll listener, no work on the main thread between
 * intersections.
 *
 * Fires **once** per element. A section that fades back out when you scroll up
 * and in again when you scroll down is a page that will not sit still, and it
 * makes re-finding something you just read genuinely harder.
 *
 * Two safety valves, because `reveal` starts invisible and anything that
 * prevents this hook from running would hide content permanently:
 *
 *   - No IntersectionObserver (very old browsers, some test runners) ⇒ visible
 *     immediately rather than never.
 *   - Reduced motion ⇒ visible immediately, and `globals.css` also refuses to
 *     hide it in the first place. Belt and braces on purpose: this is the failure
 *     mode where a nice-to-have becomes a blank page.
 */

import { useEffect, useRef, useState } from "react";

export function useInView<T extends HTMLElement = HTMLDivElement>(
  /** How much of the element must be showing. A section is "arrived" well before
      it is fully on screen, so this is low by default. */
  threshold = 0.12,
) {
  const ref = useRef<T>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduced || typeof IntersectionObserver === "undefined") {
      setInView(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        setInView(true);
        observer.disconnect();
      },
      // The bottom margin means a section starts arriving slightly before it
      // technically enters the viewport, so it is already settled by the time it
      // is actually being read.
      { threshold, rootMargin: "0px 0px -8% 0px" },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [threshold]);

  return { ref, inView, props: { "data-inview": inView } as const };
}
