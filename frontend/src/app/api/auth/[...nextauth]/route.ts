/**
 * @fileoverview Auth.js v5 route handler.
 *
 * Exposes the GET and POST handlers required by NextAuth under the
 * App Router catch-all route `/api/auth/[...nextauth]`.
 */

export { handlers as GET, handlers as POST } from "@/lib/auth";
