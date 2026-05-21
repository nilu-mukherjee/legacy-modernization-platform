/**
 * Root Layout
 * ===========
 * The top-level layout that wraps every page. Sets up:
 * - Google Fonts (Inter)
 * - Global CSS import
 * - HTML metadata for SEO
 */

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

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
      <body className={`${inter.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  );
}
