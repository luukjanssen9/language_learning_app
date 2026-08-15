import { api } from "./client";
import type { User } from "./types";

export const authApi = {
  signInWithGoogle: (credential: string) => api.post<User>("/auth/google", { credential }),
  logout: () => api.post<void>("/auth/logout"),
  me: () => api.get<User>("/auth/me"),
};
