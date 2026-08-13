import { api } from "./client";
import type { User, UserCreatePayload } from "./types";

export const usersApi = {
  list: () => api.get<User[]>("/users"),
  create: (payload: UserCreatePayload) => api.post<User>("/users", payload),
};
