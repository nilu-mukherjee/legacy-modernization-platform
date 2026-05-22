"use client";

import { useEffect } from "react";
import { SessionProvider, useSession } from "next-auth/react";
import { setAuthToken } from "@/lib/api-client";

function TokenSyncer() {
  const { data: session } = useSession();
  useEffect(() => {
    const token = (session as Record<string, unknown> | null)
      ?.backendToken as string | undefined;
    setAuthToken(token ?? null);
  }, [session]);
  return null;
}

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <TokenSyncer />
      {children}
    </SessionProvider>
  );
}
