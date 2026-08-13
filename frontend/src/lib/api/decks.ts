import { api } from "./client";
import type { Deck, DeckCreatePayload } from "./types";

export const decksApi = {
  list: () => api.get<Deck[]>("/decks"),
  create: (payload: DeckCreatePayload) => api.post<Deck>("/decks", payload),
};
