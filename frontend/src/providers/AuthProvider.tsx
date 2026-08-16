"use client";

import { GoogleLogin, GoogleOAuthProvider, type CredentialResponse } from "@react-oauth/google";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useContext, useState, type ReactNode } from "react";
import { authApi } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? "";

interface AuthContextValue {
  userId: string;
  email: string;
  displayName: string;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuthContext(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuthContext must be used within AuthProvider");
  }
  return ctx;
}

// In-place login gate (Phase 8 slice 4): wraps the whole app, ahead of
// BootstrapProvider. A signed-out visitor sees the Google sign-in screen
// rendered here instead of `children` -- same URL, no redirect, no
// Next.js middleware -- replacing the standalone /login page slice 1
// used to prove the mechanism worked.
export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const {
    data: user,
    isPending,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: authApi.me,
    retry: false,
  });

  async function logout() {
    await authApi.logout();
    // Wipes every cached query, not just auth -- a real user switch
    // shouldn't show the previous user's stale decks/vocabulary for even
    // a moment. Safe to do unconditionally: once refetch() below settles
    // into the 401 state, AuthProvider renders the sign-in gate instead
    // of `children`, unmounting the whole app tree anyway.
    queryClient.clear();
    await refetch();
  }

  if (isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-ink-soft">Loading…</div>
    );
  }

  // A non-401 error (network down, backend unreachable) isn't "signed
  // out" -- surface it distinctly rather than silently showing the
  // sign-in screen, which would look like nothing is wrong.
  if (isError && (!(error instanceof ApiError) || error.status !== 401)) {
    return (
      <div className="flex min-h-dvh items-center justify-center p-6 text-center text-ink-soft">
        Couldn&apos;t reach the API at{" "}
        {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}. Confirm the backend is
        running and reload.
      </div>
    );
  }

  if (!user) {
    return <SignInGate onSuccess={() => refetch()} />;
  }

  const value: AuthContextValue = {
    userId: user.id,
    email: user.email,
    displayName: user.display_name,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function SignInGate({ onSuccess }: { onSuccess: () => void }) {
  const [error, setError] = useState<string | null>(null);

  async function handleSuccess(response: CredentialResponse) {
    setError(null);
    if (!response.credential) {
      setError("Google didn't return a credential.");
      return;
    }
    try {
      await authApi.signInWithGoogle(response.credential);
      onSuccess();
    } catch {
      setError("Sign-in failed. Try again.");
    }
  }

  if (!GOOGLE_CLIENT_ID) {
    return (
      <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-4 p-6 text-center">
        <p className="text-ink-soft">
          NEXT_PUBLIC_GOOGLE_CLIENT_ID isn&apos;t set — see frontend/.env.example.
        </p>
      </main>
    );
  }

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-4 p-6 text-center">
        <h1 className="font-display text-3xl text-ink">Sign in</h1>
        <GoogleLogin
          onSuccess={handleSuccess}
          onError={() => setError("Sign-in failed. Try again.")}
        />
        {error && <p className="text-sm text-rating-again">{error}</p>}
      </main>
    </GoogleOAuthProvider>
  );
}
