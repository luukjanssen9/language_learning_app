import { api } from "./client";
import type {
  Card,
  CardCreatePayload,
  CardQuickAddPayload,
  CardQuickAddResponse,
  CardReviewResponse,
  CardUpdatePayload,
  ReviewRating,
} from "./types";

export const cardsApi = {
  list: (deckId: string) =>
    api.get<Card[]>(`/cards?${new URLSearchParams({ deck_id: deckId })}`),
  // newLimit is omitted from the query by default (not defaulted to a
  // fixed number) so the backend's own deck.daily_new_card_cap logic
  // actually takes effect -- an explicit value here overrides it, same
  // as the backend route's own new_limit param semantics.
  due: (deckId: string, dueLimit = 100, newLimit?: number) => {
    const params = new URLSearchParams({ deck_id: deckId, due_limit: String(dueLimit) });
    if (newLimit !== undefined) params.set("new_limit", String(newLimit));
    return api.get<Card[]>(`/cards/due?${params}`);
  },
  create: (payload: CardCreatePayload) => api.post<Card>("/cards", payload),
  quickAdd: (payload: CardQuickAddPayload) =>
    api.post<CardQuickAddResponse>("/cards/quick-add", payload),
  update: (id: string, payload: CardUpdatePayload) => api.patch<Card>(`/cards/${id}`, payload),
  remove: (id: string) => api.delete(`/cards/${id}`),
  review: (id: string, rating: ReviewRating) =>
    api.post<CardReviewResponse>(`/cards/${id}/review`, { rating }),
};
