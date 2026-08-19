"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * An index that advances on its own, and stops the moment anyone touches it.
 *
 * The demo section learned the hard way that auto-advance is wrong for content
 * someone is *reading* — it moves while you are mid-sentence. A gallery is the
 * other case: nobody reads a carousel of illustrations in order, and rotating it
 * shows what is on offer without eight tiles competing for the same space. So it
 * rotates, but under three conditions, and all three matter:
 *
 *   - **It stops permanently on interaction.** Hover, focus, or a click and it
 *     never starts again for that visit. An auto-advance that resumes after you
 *     look away is one that fights you for control of the thing you are reading.
 *   - **It only runs on screen.** An interval ticking under the fold is a
 *     wakelock on someone's phone for a section they cannot see.
 *   - **It never runs under `prefers-reduced-motion`**, where it simply shows the
 *     first item and waits to be asked.
 */
export function useCarousel(count: number, intervalMs = 4200) {
  const [index, setIndex] = useState(0);
  const [stopped, setStopped] = useState(false);
  const [visible, setVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node || typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }

    const observer = new IntersectionObserver(([entry]) => setVisible(entry.isIntersecting), {
      threshold: 0.3,
    });
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (stopped || !visible || count < 2) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;

    const timer = setInterval(() => setIndex((i) => (i + 1) % count), intervalMs);
    return () => clearInterval(timer);
  }, [stopped, visible, count, intervalMs]);

  /** Take over. Called from pointer, focus and click handlers alike. */
  const take = useCallback((next?: number) => {
    setStopped(true);
    if (next !== undefined) setIndex(next);
  }, []);

  return { ref, index, stopped, take };
}
