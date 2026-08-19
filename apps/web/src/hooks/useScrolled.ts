"use client";

import { useEffect, useState } from "react";

/**
 * Whether the page has been scrolled past a threshold.
 *
 * For the header, which sits flush with the hero at rest and only earns its
 * border and shadow once there is content underneath it. A bar that is divided
 * off from the page before anything has moved is drawing a line for no reason;
 * the line means "there is more above you", and at the top of the page that is
 * not true yet.
 *
 * `passive: true` matters here. A non-passive scroll listener tells the browser
 * the handler might call `preventDefault`, so it cannot start scrolling until
 * the handler returns — on a long landing page that is the difference between
 * smooth scrolling and a stutter.
 */
export function useScrolled(threshold = 8): boolean {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const read = () => setScrolled(window.scrollY > threshold);

    // Read once on mount: a reload halfway down the page restores the scroll
    // position without ever firing an event, and the header would come back
    // borderless over content it is sitting on top of.
    read();

    window.addEventListener("scroll", read, { passive: true });
    return () => window.removeEventListener("scroll", read);
  }, [threshold]);

  return scrolled;
}
