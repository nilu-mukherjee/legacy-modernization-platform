/**
 * @fileoverview Next.js middleware for route protection.
 *
 * Redirects unauthenticated users away from protected routes (dashboard,
 * projects, settings) to the login page.  Public routes (landing page,
 * login, API, static assets) are always accessible.
 */

export { auth as middleware } from "@/lib/auth";

/**
 * Matcher config — only run the middleware on routes that need protection.
 *
 * Excludes:
 * - `/` (landing page)
 * - `/login`
 * - `/api/auth/*` (NextAuth endpoints)
 * - `/_next/*` (Next.js internals)
 * - Static files (favicon, images, etc.)
 */
export const config = {
  matcher: [
    /*
     * Match all request paths EXCEPT:
     * - api/auth (NextAuth routes)
     * - _next/static (static files)
     * - _next/image (optimized images)
     * - favicon.ico, sitemap.xml, robots.txt
     * - / (landing page — handled by the marketing layout)
     */
    "/((?!api/auth|_next/static|_next/image|favicon\\.ico|sitemap\\.xml|robots\\.txt).*)",
  ],
};
