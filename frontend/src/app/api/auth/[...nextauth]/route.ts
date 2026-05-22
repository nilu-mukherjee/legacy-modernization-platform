/**
 * @fileoverview Auth.js v5 route handler.
 *
 * Exposes the GET and POST handlers required by NextAuth under the
 * App Router catch-all route `/api/auth/[...nextauth]`.
 */

import { handlers } from "@/lib/auth";
export const { GET, POST } = handlers;
