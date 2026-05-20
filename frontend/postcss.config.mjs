/**
 * @fileoverview PostCSS configuration for Tailwind CSS v4.
 *
 * Uses the new `@tailwindcss/postcss` plugin which replaces the legacy
 * `tailwindcss` PostCSS plugin and includes built-in autoprefixing.
 */

/** @type {import('postcss-load-config').Config} */
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
