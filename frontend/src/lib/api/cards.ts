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
  list: (deckId: string, userId: string) =>
    api.get<Card[]>(`/cards?${new URLSearchParams({ deck_id: deckId, user_id: userId })}`),
  // newLimit is omitted from the query by default (not defaulted to a
  // fixed number) so the backend's own deck.daily_new_card_cap logic
  // actually takes effect -- an explicit value here overrides it, same
  // as the backend route's own new_limit param semantics.
  due: (deckId: string, userId: string, dueLimit = 100, newLimit?: number) => {
    const params = new URLSearchParams({
      deck_id: deckId,
      user_id: userId,
      due_limit: String(dueLimit),
    });
    if (newLimit !== undefined) params.set("new_limit", String(newLimit));
    return api.get<Card[]>(`/cards/due?${params}`);
  },
  create: (userId: string, payload: CardCreatePayload) =>
    api.post<Card>(`/cards?${new URLSearchParams({ user_id: userId })}`, payload),
  quickAdd: (userId: string, payload: CardQuickAddPayload) =>
    api.post<CardQuickAddResponse>(
      `/cards/quick-add?${new URLSearchParams({ user_id: userId })}`,
      payload,
    ),
  update: (id: string, userId: string, payload: CardUpdatePayload) =>
    api.patch<Card>(`/cards/${id}?${new URLSearchParams({ user_id: userId })}`, payload),
  remove: (id: string, userId: string) =>
    api.delete(`/cards/${id}?${new URLSearchParams({ user_id: userId })}`),
  review: (id: string, userId: string, rating: ReviewRating) =>
    api.post<CardReviewResponse>(
      `/cards/${id}/review?${new URLSearchParams({ user_id: userId })}`,
      { rating },
    ),
};
