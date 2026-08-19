"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Turns scroll position through a tall element into a step index.
 *
 * For sequences the reader should drive rather than watch. A timer advancing a
 * demo on its own is the worst version of this: it moves while you are still
 * reading step two, and it moves again while you are trying to find where step
 * two went. Tying it to scroll means the sequence only ever advances because
 * someone asked it to, and it runs backwards just as willingly.
 *
 * The element this attaches to is deliberately much taller than the viewport —
 * that extra height *is* the scrub track. What the reader sees is the sticky
 * child inside it, which stays put while the track passes behind.
 *
 * Measurement happens in a rAF rather than in the scroll handler. Reading
 * `getBoundingClientRect` forces layout, and doing that on every scroll event on
 * a long page is the classic way to make scrolling stutter.
 */
export function useScrollSteps<T extends HTMLElement>(count: number) {
  const ref = useRef<T>(null);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const node = ref.current;
    if (!node || count < 1) return;

    let frame = 0;

    const measure = () => {
      frame = 0;
      const rect = node.getBoundingClientRect();

      // How far the track has travelled, as 0..1. `rect.height - innerHeight` is
      // the distance it can travel while any part of it is still on screen; on a
      // viewport taller than the track that goes negative, so it is floored at 1
      // to avoid dividing by zero and to leave the last step showing.
      const travel = rect.height - window.innerHeight;
      const progress = travel > 0 ? -rect.top / travel : 0;
      const clamped = Math.min(1, Math.max(0, progress));

      // `count - 1` rather than `count`: at progress exactly 1 the floor would
      // otherwise land one past the end.
      setIndex(Math.min(count - 1, Math.floor(clamped * count)));
    };

    const onScroll = () => {
      if (frame) return;
      frame = requestAnimationFrame(measure);
    };

    measure();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });

    return () => {
      if (frame) cancelAnimationFrame(frame);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, [count]);

  /**
   * Scroll to the segment that shows `target`.
   *
   * Clicking a step has to move the page, not just set state — with scroll
   * driving the index, setting it directly would be undone by the next scroll
   * event and the step would snap back. Aiming at the middle of the segment
   * keeps a click from landing on the boundary between two.
   */
  const scrollTo = (target: number) => {
    const node = ref.current;
    if (!node) return;

    const travel = node.offsetHeight - window.innerHeight;
    if (travel <= 0) return;

    const middle = (target + 0.5) / count;
    window.scrollTo({
      top: node.offsetTop + travel * middle,
      behavior: "smooth",
    });
  };

  return { ref, index, scrollTo };
}
