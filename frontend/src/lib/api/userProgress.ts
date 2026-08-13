import { api } from "./client";
import type { UserProgress } from "./types";

export const userProgressApi = {
  list: (userId: string) =>
    api.get<UserProgress[]>(`/user-progress?${new URLSearchParams({ user_id: userId })}`),
};
