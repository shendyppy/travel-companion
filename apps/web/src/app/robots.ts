import type { MetadataRoute } from "next";

const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

/**
 * `/flights` is disallowed here as well as being `noindex`.
 *
 * The two do different jobs and both are wanted: `noindex` keeps results out of
 * the index but a crawler still has to fetch the page to read the tag, and every
 * one of those fetches can reach a paid flight provider. Disallow stops the
 * request before it happens.
 */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/api/", "/id/flights", "/en/flights", "/id/chat", "/en/chat"],
    },
    sitemap: `${SITE}/sitemap.xml`,
  };
}
