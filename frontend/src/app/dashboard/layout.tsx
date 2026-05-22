/**
 * Dashboard Layout
 * ================
 * Protected layout with sidebar navigation and header.
 * Wraps all dashboard pages.
 */

import Link from "next/link";
import {
  LayoutDashboard,
  FolderGit2,
  BarChart3,
  Bot,
  FileCode2,
  Settings,
  LogOut,
} from "lucide-react";
import { auth } from "@/lib/auth";
import { signOutAction } from "./actions";

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: "Overview", href: "/dashboard" },
  { icon: FolderGit2, label: "Projects", href: "/dashboard/projects" },
  { icon: BarChart3, label: "Analytics", href: "/dashboard/analytics" },
  { icon: Bot, label: "AI Insights", href: "/dashboard/insights" },
];

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();
  const userName = session?.user?.name ?? "User";
  const userInitial = userName.charAt(0).toUpperCase();
  return (
    <div className="flex min-h-screen">
      {/* ── Sidebar ───────────────────────────────────────────────── */}
      <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-border bg-card">
        {/* Logo */}
        <div className="flex h-16 items-center gap-2 border-b border-border px-6">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg gradient-primary">
            <FileCode2 className="h-4 w-4 text-white" />
          </div>
          <span className="text-lg font-bold">CodeLens AI</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          ))}
        </nav>

        {/* Bottom section */}
        <div className="border-t border-border p-3">
          <Link
            href="/dashboard/settings"
            className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <Settings className="h-4 w-4" />
            Settings
          </Link>
          <form action={signOutAction}>
            <button
              type="submit"
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <LogOut className="h-4 w-4" />
              Sign Out
            </button>
          </form>
        </div>
      </aside>

      {/* ── Main Content ──────────────────────────────────────────── */}
      <main className="ml-64 flex-1">
        {/* Top Header */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background/80 px-8 backdrop-blur-sm">
          <div>
            <h2 className="text-lg font-semibold">Dashboard</h2>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">{userName}</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-sm font-bold text-primary">
              {userInitial}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="p-8">{children}</div>
      </main>
    </div>
  );
}
