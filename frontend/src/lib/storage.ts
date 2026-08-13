import type { BootstrapResult } from "./bootstrap";

const STORAGE_KEY = "language-app:bootstrap";

export function readBootstrapCache(): BootstrapResult | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as BootstrapResult;
  } catch {
    return null;
  }
}

export function writeBootstrapCache(result: BootstrapResult): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(result));
}

export function clearBootstrapCache(): void {
  window.localStorage.removeItem(STORAGE_KEY);
}
