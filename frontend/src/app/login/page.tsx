"use client";

import { GoogleLogin, GoogleOAuthProvider, type CredentialResponse } from "@react-oauth/google";
import { useState } from "react";
import { authApi } from "@/lib/api/auth";
import type { User } from "@/lib/api/types";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? "";

// Phase 8 slice 1: proves the Google sign-in round trip works end to end,
// deliberately standalone -- not yet linked from Nav.tsx or wired into
// BootstrapProvider (which still silently creates/reuses its own single
// dev user on every page, this one included, for now). That replacement
// is a later slice's job; this page exists to verify the mechanism itself
// first, since it's the one piece that needs a real Google account
// clicking through a real consent screen to confirm.
export default function LoginPage() {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSuccess(response: CredentialResponse) {
    setError(null);
    if (!response.credential) {
      setError("Google didn't return a credential.");
      return;
    }
    try {
      const signedInUser = await authApi.signInWithGoogle(response.credential);
      setUser(signedInUser);
    } catch {
      setError("Sign-in failed. Try again.");
    }
  }

  async function handleLogout() {
    await authApi.logout();
    setUser(null);
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
        {user ? (
          <div className="flex flex-col items-center gap-3">
            <p className="text-ink">
              Signed in as {user.display_name} ({user.email})
            </p>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-md border border-line px-4 py-2 text-sm font-medium text-ink"
            >
              Log out
            </button>
          </div>
        ) : (
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={() => setError("Sign-in failed. Try again.")}
          />
        )}
        {error && <p className="text-sm text-rating-again">{error}</p>}
      </main>
    </GoogleOAuthProvider>
  );
}
