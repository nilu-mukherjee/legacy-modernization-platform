/**
 * Login Page
 * ==========
 * GitHub OAuth sign-in page with premium dark design.
 */

import Link from "next/link";
import { FileCode2 } from "lucide-react";
import { signInWithGitHub } from "./actions";

export const metadata = {
  title: "Sign In",
};

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-6">
      {/* Background effects */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-1/2 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/5 blur-[120px]" />
      </div>

      <div className="relative w-full max-w-md animate-[slide-up_0.5s_ease-out]">
        {/* Logo */}
        <div className="mb-8 text-center">
          <Link href="/" className="inline-flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl gradient-primary">
              <FileCode2 className="h-5 w-5 text-white" />
            </div>
            <span className="text-2xl font-bold">CodeLens AI</span>
          </Link>
        </div>

        {/* Card */}
        <div className="glass rounded-2xl p-8 glow-border">
          <h1 className="mb-2 text-center text-2xl font-bold">Welcome back</h1>
          <p className="mb-8 text-center text-sm text-muted-foreground">
            Sign in with your GitHub account to continue
          </p>

          {/* GitHub OAuth Button — Server Action lets Auth.js handle CSRF internally */}
          <form action={signInWithGitHub}>
            <button
              type="submit"
              className="group flex w-full items-center justify-center gap-3 rounded-xl bg-white px-6 py-3.5 text-base font-semibold text-gray-900 transition-all hover:bg-gray-100 hover:shadow-lg"
            >
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
              Continue with GitHub
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-muted-foreground">
            We only request read access to your repositories.
            <br />
            Your code never leaves our secure servers.
          </p>
        </div>
      </div>
    </div>
  );
}
