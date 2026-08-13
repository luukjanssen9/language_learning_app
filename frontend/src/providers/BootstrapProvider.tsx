"use client";

import { useQuery } from "@tanstack/react-query";
import { createContext, useContext, type ReactNode } from "react";
import { ensureBootstrap, type BootstrapResult } from "@/lib/bootstrap";

const BootstrapContext = createContext<BootstrapResult | null>(null);

export function useBootstrapContext(): BootstrapResult {
  const ctx = useContext(BootstrapContext);
  if (!ctx) {
    throw new Error("useBootstrapContext must be used within BootstrapProvider");
  }
  return ctx;
}

export function BootstrapProvider({ children }: { children: ReactNode }) {
  const { data, isPending, isError } = useQuery({
    queryKey: ["bootstrap"],
    queryFn: ensureBootstrap,
    staleTime: Infinity,
    retry: 1,
  });

  if (isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-ink-soft">Loading…</div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex min-h-dvh items-center justify-center p-6 text-center text-ink-soft">
        Couldn&apos;t reach the API at{" "}
        {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}. Confirm the backend is
        running and reload.
      </div>
    );
  }

  return <BootstrapContext.Provider value={data}>{children}</BootstrapContext.Provider>;
}
