import { api } from "./client";
import type { Deck, DeckCreatePayload, DeckUpdatePayload } from "./types";

export const decksApi = {
  list: () => api.get<Deck[]>("/decks"),
  create: (payload: DeckCreatePayload) => api.post<Deck>("/decks", payload),
  update: (id: string, payload: DeckUpdatePayload) => api.patch<Deck>(`/decks/${id}`, payload),
  remove: (id: string) => api.delete(`/decks/${id}`),
};
