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
    async jwt({ token, account, profile }) {
      if (account) {
        token.accessToken = account.access_token;
        token.githubUsername = profile?.login;
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
        (session as Record<string, unknown>).accessToken =
          token.accessToken;
      }
      if (token.githubUsername) {
        (session.user as Record<string, unknown>).githubUsername =
          token.githubUsername;
      }
      return session;
    },

    /**
     * Authorized callback — controls whether a request is allowed.
     *
     * Returns true for all requests (route protection is handled by
     * middleware instead).
     */
    authorized({ auth: sessionAuth }) {
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
