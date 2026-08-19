import { NextResponse, type NextRequest } from "next/server";
import { LOCALES, isLocale, matchLocale } from "@/lib/i18n";

/**
 * Puts a locale on every URL.
 *
 * Locale lives in the path rather than in a cookie because this page gets
 * shared. A recruiter in Berlin opening a link someone sent them should get
 * English, and Google should be able to index both versions separately — neither
 * works if the language is a preference stored in the reader's own browser.
 *
 * A visitor's `Accept-Language` decides only the *first* redirect. After that
 * the URL is the truth: someone who deliberately switched to English and then
 * bookmarked the page must not be bounced back to Indonesian by their browser
 * settings on the next visit.
 */
export default function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const hasLocale = LOCALES.some(
    (locale) => pathname === `/${locale}` || pathname.startsWith(`/${locale}/`),
  );
  if (hasLocale) return NextResponse.next();

  // A returning visitor's own choice, remembered from the last switch. Only
  // consulted when the path has no locale of its own to go on.
  const remembered = request.cookies.get("tc:locale")?.value;
  const locale = isLocale(remembered)
    ? remembered
    : matchLocale(request.headers.get("accept-language"));

  const url = request.nextUrl.clone();
  url.pathname = `/${locale}${pathname === "/" ? "" : pathname}`;

  // 307, not 308: which locale a bare path resolves to depends on who is asking,
  // so it must not be cached as permanent by anyone in between.
  return NextResponse.redirect(url, 307);
}

export const config = {
  // Everything except Next internals, the metadata files Next serves from the
  // app root, and anything with a file extension. A locale prefix on
  // /sitemap.xml would break it.
  matcher: ["/((?!_next|api|.*\\..*).*)"],
};
