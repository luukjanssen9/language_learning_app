"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

export function QueryProvider({ children }: { children: ReactNode }) {
  // useState(() => new QueryClient()) rather than a module-level singleton:
  // this file is a client component, but a naive module-level instance
  // would still be a footgun if this ever runs anywhere server-adjacent --
  // this is the documented pattern for guaranteeing one client per mount,
  // never shared across requests.
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
      }),
  );

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
