/*
 * Copyright (c) 2026 Nilu Mukherjee.
 * Licensed under AGPL-3.0. See LICENSE at repo root.
 */

/**
 * @fileoverview Auth.js v5 (NextAuth) configuration for CodeLens AI.
 *
 * Provides GitHub OAuth authentication with:
 * - Repository scope for reading user repos
 * - JWT callback to persist the access token
 * - Session callback to expose the token to client components
 * - Sign-in event to sync the user profile to the backend
 */

import NextAuth from "next-auth";
import GitHub from "next-auth/providers/github";

/**
 * Auth.js configuration and exported handlers / helpers.
 *
 * `handlers` — Route handlers for `/api/auth/*`
 * `auth`     — Server-side session accessor
 * `signIn`   — Programmatic sign-in trigger
 * `signOut`  — Programmatic sign-out trigger
 */
export const { handlers, auth, signIn, signOut } = NextAuth({
  trustHost: true,

  /** Registered OAuth providers. */
  providers: [
    GitHub({
      clientId: process.env.AUTH_GITHUB_ID,
      clientSecret: process.env.AUTH_GITHUB_SECRET,
      authorization: {
        params: {
          scope: "read:user user:email repo",
        },
      },
    }),
  ],

  /** Use the default pages with a custom sign-in path. */
  pages: {
    signIn: "/login",
  },

  /** JWT-based session strategy (no database required). */
  session: {
    strategy: "jwt",
  },

  callbacks: {
    /**
     * JWT callback — runs whenever a JSON Web Token is created or updated.
     *
     * On initial sign-in, we persist the GitHub access token and user
     * profile into the JWT so downstream callbacks can access them.
     */
    async jwt({ token, account, user, profile }) {
      if (account) {
        token.accessToken = account.access_token;
        token.githubUsername = (profile as Record<string, unknown>)?.login as string | undefined;
      }

      // Sync (or re-sync) to backend whenever backendToken is missing.
      if (!token.backendToken && token.accessToken && token.sub) {
        try {
          const apiUrl = process.env.INTERNAL_API_URL || "http://localhost:8000";
          const res = await fetch(`${apiUrl}/api/v1/auth/sync`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              github_id: String(
                (profile as Record<string, unknown>)?.id ?? user?.id ?? token.sub
              ),
              email: user?.email ?? token.email,
              name: user?.name ?? token.name,
              avatar_url: user?.image,
              access_token: token.accessToken,
            }),
          });
          if (res.ok) {
            const data = (await res.json()) as { token: string };
            token.backendToken = data.token;
          } else {
            console.error("[Auth] Backend sync failed:", res.status, await res.text());
          }
        } catch (err) {
          console.error("[Auth] Backend sync error:", err);
        }
      }

      return token;
    },

    /**
     * Session callback — shapes the session object exposed to the client.
     *
     * Copies the access token and GitHub username from the JWT into the
     * session so `useSession()` / `auth()` callers can read them.
     */
    async session({ session, token }) {
      if (token.accessToken) {
        (session as unknown as Record<string, unknown>).accessToken =
          token.accessToken;
      }
      if (token.githubUsername) {
        (session.user as unknown as Record<string, unknown>).githubUsername =
          token.githubUsername;
      }
      if (token.backendToken) {
        (session as unknown as Record<string, unknown>).backendToken =
          token.backendToken;
      }
      return session;
    },

    /**
     * Authorized callback — controls whether a request is allowed.
     *
     * Public routes (landing, login, report sharing) are always allowed.
     * Signed-in users on /login get redirected to /dashboard.
     * All other routes require authentication.
     */
    authorized({ auth: sessionAuth, request }) {
      const { pathname } = request.nextUrl;
      const PUBLIC_PATHS = ["/", "/login"];
      const isPublic =
        PUBLIC_PATHS.includes(pathname) || pathname.startsWith("/report/");

      if (sessionAuth && pathname === "/login") {
        return Response.redirect(new URL("/dashboard", request.nextUrl));
      }
      if (isPublic) return true;
      return !!sessionAuth;
    },
  },

  events: {
    /**
     * Sign-in event — fires after successful authentication.
     *
     * Syncs the user profile to the CodeLens AI backend so the backend
     * can associate projects with the user.
     */
    async signIn({ user, account }) {
      // TODO: POST to backend /api/v1/auth/sync with user + accessToken
      console.log(
        `[Auth] User signed in: ${user.email} (provider: ${account?.provider})`,
      );
    },
  },
});
