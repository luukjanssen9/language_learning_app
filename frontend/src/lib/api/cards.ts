import { api } from "./client";
import type {
  Card,
  CardCreatePayload,
  CardReviewResponse,
  CardUpdatePayload,
  ReviewRating,
} from "./types";

export const cardsApi = {
  list: (deckId: string) => api.get<Card[]>(`/cards?${new URLSearchParams({ deck_id: deckId })}`),
  due: (deckId: string, newLimit = 20, dueLimit = 100) =>
    api.get<Card[]>(
      `/cards/due?${new URLSearchParams({
        deck_id: deckId,
        new_limit: String(newLimit),
        due_limit: String(dueLimit),
      })}`,
    ),
  create: (payload: CardCreatePayload) => api.post<Card>("/cards", payload),
  update: (id: string, payload: CardUpdatePayload) => api.patch<Card>(`/cards/${id}`, payload),
  remove: (id: string) => api.delete(`/cards/${id}`),
  review: (id: string, rating: ReviewRating) =>
    api.post<CardReviewResponse>(`/cards/${id}/review`, { rating }),
};
