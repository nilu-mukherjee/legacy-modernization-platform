/**
 * @fileoverview Root layout for the CodeLens AI application.
 *
 * Responsibilities:
 * - Loads the Inter font via `next/font/google`
 * - Sets the `dark` class on `<html>` for Tailwind dark-mode-first
 * - Defines global metadata (title, description)
 * - Wraps the app with the Sonner `<Toaster>` for toast notifications
 */

import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "sonner";

import "./globals.css";

/**
 * Inter font — variable weight loaded from Google Fonts.
 * Applied globally via `inter.variable` on the `<body>`.
 */
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

/** Page metadata used by Next.js for `<head>` generation. */
export const metadata: Metadata = {
  title: {
    default: "CodeLens AI — Legacy Modernization Platform",
    template: "%s | CodeLens AI",
  },
  description:
    "AI-powered platform that analyzes legacy codebases, identifies technical debt, and generates actionable modernization recommendations.",
  keywords: [
    "legacy modernization",
    "technical debt",
    "code analysis",
    "AI",
    "refactoring",
  ],
  authors: [{ name: "CodeLens AI" }],
};

/** Viewport settings — dark theme color for mobile browser chrome. */
export const viewport: Viewport = {
  themeColor: "#020617",
  width: "device-width",
  initialScale: 1,
};

/**
 * Root layout component.
 *
 * Every page in the application is wrapped by this layout which provides:
 * 1. HTML `lang` and `class="dark"` attributes
 * 2. Inter font via CSS variable
 * 3. Sonner toast provider
 *
 * @param children — nested route content
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className={`${inter.variable} font-sans antialiased`}
        suppressHydrationWarning
      >
        {children}

        {/* Global toast notification provider */}
        <Toaster
          position="bottom-right"
          toastOptions={{
            className:
              "!bg-card !text-card-foreground !border-border !shadow-xl",
          }}
          richColors
          closeButton
        />
      </body>
    </html>
  );
}
