import { api } from "./client";
import type { Language, LanguageCreatePayload } from "./types";

export const languagesApi = {
  list: () => api.get<Language[]>("/languages"),
  create: (payload: LanguageCreatePayload) => api.post<Language>("/languages", payload),
};
