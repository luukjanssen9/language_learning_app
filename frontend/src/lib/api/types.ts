// Hand-written to match backend/app/schemas/*.py field-for-field. Not
// generated from the OpenAPI schema -- at this phase's scope (~6 resources)
// reviewing directly against the Pydantic source is faster and easier to
// reason about than wiring in a codegen step. Revisit if the schema surface
// grows a lot.

export type ScriptDirection = "ltr" | "rtl";
export type CardDirection = "target_to_base" | "base_to_target" | "mixed";
export type CardState = "new" | "learning" | "review" | "relearning";
export type ReviewRating = "again" | "hard" | "good" | "easy";

export interface Language {
  id: string;
  code: string;
  name: string;
  script_direction: ScriptDirection;
  grammar_config: Record<string, unknown>;
  created_at: string;
}

export interface Course {
  id: string;
  base_language_id: string;
  target_language_id: string;
  name: string;
  slug: string;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  display_name: string;
  created_at: string;
}

export interface Deck {
  id: string;
  user_id: string;
  course_id: string;
  name: string;
  description: string | null;
  created_at: string;
}

export interface Card {
  id: string;
  deck_id: string;
  vocabulary_item_id: string | null;
  front_override: string | null;
  back_override: string | null;
  direction: CardDirection;
  created_at: string;
  state: CardState;
  step: number | null;
  stability: number | null;
  difficulty: number | null;
  due_at: string | null;
  reps: number;
  lapses: number;
  last_reviewed_at: string | null;
}

export interface ReviewLog {
  id: string;
  card_id: string;
  reviewed_at: string;
  rating: ReviewRating;
  elapsed_days: number | null;
  scheduled_days: number | null;
  state_before: CardState | null;
}

export interface CardReviewResponse {
  card: Card;
  review_log: ReviewLog;
}

export interface LanguageCreatePayload {
  code: string;
  name: string;
}

export interface CourseCreatePayload {
  base_language_id: string;
  target_language_id: string;
  name: string;
  slug: string;
}

export interface UserCreatePayload {
  email: string;
  display_name: string;
}

export interface DeckCreatePayload {
  user_id: string;
  course_id: string;
  name: string;
  description?: string | null;
}

export interface CardCreatePayload {
  deck_id: string;
  vocabulary_item_id?: string | null;
  front_override?: string | null;
  back_override?: string | null;
  direction?: CardDirection;
}

export interface CardUpdatePayload {
  front_override?: string;
  back_override?: string;
  direction?: CardDirection;
}
