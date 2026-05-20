/**
 * @fileoverview Next.js 15 configuration for the CodeLens AI frontend.
 *
 * Configures:
 * - Standalone output mode for optimized Docker deployments
 * - Image optimization with remote pattern allowlist
 * - Environment variable forwarding to the client bundle
 * - Strict React mode for development correctness checks
 */

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /** Produce a self-contained build for Docker (no node_modules needed). */
  output: "standalone",

  /** Enable React strict mode to surface subtle bugs during development. */
  reactStrictMode: true,

  /** Image optimization configuration. */
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "avatars.githubusercontent.com",
        port: "",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "github.com",
        port: "",
        pathname: "/**",
      },
    ],
  },

  /** Forward selected environment variables to the client bundle. */
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
  },

  /** Suppress noisy warnings from third-party packages during builds. */
  eslint: {
    ignoreDuringBuilds: false,
  },

  typescript: {
    ignoreBuildErrors: false,
  },
};

export default nextConfig;
