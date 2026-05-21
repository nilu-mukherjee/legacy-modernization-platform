/**
 * Projects List Page
 * ==================
 * Displays all user projects in a card grid with status badges.
 */

import Link from "next/link";
import {
  FolderGit2,
  Plus,
  Clock,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from "lucide-react";

export const metadata = {
  title: "Projects",
};

/** Map project status to icon and color. */
function statusDisplay(status: string) {
  switch (status) {
    case "completed":
      return { icon: CheckCircle2, label: "Completed", color: "text-success" };
    case "analyzing":
      return { icon: Loader2, label: "Analyzing", color: "text-primary" };
    case "failed":
      return { icon: AlertCircle, label: "Failed", color: "text-destructive" };
    default:
      return { icon: Clock, label: "Pending", color: "text-muted-foreground" };
  }
}

export default function ProjectsPage() {
  // In the MVP, this will fetch from the API client-side.
  // For now, render the empty state and "New Project" action.

  return (
    <div className="space-y-6 animate-[fade-in_0.5s_ease-out]">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Projects</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage your repository analyses
          </p>
        </div>
        <Link
          href="/dashboard/projects/new"
          className="inline-flex items-center gap-2 rounded-xl gradient-primary px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-primary/25 transition-all hover:shadow-xl"
        >
          <Plus className="h-4 w-4" />
          New Project
        </Link>
      </div>

      {/* Empty State */}
      <div className="glass rounded-xl p-12 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
          <FolderGit2 className="h-8 w-8 text-primary" />
        </div>
        <h3 className="mb-2 text-xl font-semibold">No projects yet</h3>
        <p className="mb-6 text-muted-foreground">
          Add a GitHub repository to start analyzing.
        </p>
        <Link
          href="/dashboard/projects/new"
          className="inline-flex items-center gap-2 rounded-xl gradient-primary px-6 py-3 text-sm font-semibold text-white"
        >
          <Plus className="h-4 w-4" />
          Add Repository
        </Link>
      </div>
    </div>
  );
}
