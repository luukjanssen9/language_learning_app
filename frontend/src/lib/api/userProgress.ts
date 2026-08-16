import { api } from "./client";
import type { UserProgress } from "./types";

export const userProgressApi = {
  list: () => api.get<UserProgress[]>("/user-progress"),
};
