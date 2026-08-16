import { api } from "./client";
import type { Deck, DeckCreatePayload, DeckUpdatePayload } from "./types";

export const decksApi = {
  list: (userId: string) => api.get<Deck[]>(`/decks?${new URLSearchParams({ user_id: userId })}`),
  create: (payload: DeckCreatePayload) => api.post<Deck>("/decks", payload),
  update: (id: string, userId: string, payload: DeckUpdatePayload) =>
    api.patch<Deck>(`/decks/${id}?${new URLSearchParams({ user_id: userId })}`, payload),
  remove: (id: string, userId: string) =>
    api.delete(`/decks/${id}?${new URLSearchParams({ user_id: userId })}`),
};
