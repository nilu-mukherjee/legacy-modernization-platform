/**
 * Root Layout
 * ===========
 * The top-level layout that wraps every page. Sets up:
 * - IBM Plex Sans (via @fontsource)
 * - Global CSS import
 * - HTML metadata for SEO
 */

import type { Metadata } from "next";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/ibm-plex-sans/700.css";
import "./globals.css";
import Providers from "./providers";

export const metadata: Metadata = {
  title: {
    template: "%s | CodeLens AI",
    default: "CodeLens AI — AI-Powered Legacy Modernization",
  },
  description:
    "Analyze repositories, detect technical debt, and generate AI-powered modernization recommendations.",
  keywords: [
    "legacy modernization",
    "technical debt",
    "code analysis",
    "AI",
    "refactoring",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
