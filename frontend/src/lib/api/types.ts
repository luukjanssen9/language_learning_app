// Hand-written to match backend/app/schemas/*.py field-for-field. Not
// generated from the OpenAPI schema -- at this phase's scope (~6 resources)
// reviewing directly against the Pydantic source is faster and easier to
// reason about than wiring in a codegen step. Revisit if the schema surface
// grows a lot.

export type ScriptDirection = "ltr" | "rtl";
export type CardDirection = "target_to_base" | "base_to_target" | "mixed";
export type CardState = "new" | "learning" | "review" | "relearning";
export type ReviewRating = "again" | "hard" | "good" | "easy";
export type ExerciseType =
  | "multiple_choice"
  | "translation"
  | "fill_in_blank"
  | "free_text"
  | "conjugation";

// One entry of Language.grammar_config.practice_categories -- read via a
// loose cast where consumed (grammar_config itself stays a flexible bag,
// not fully typed) since this shape is a frontend-side convention this
// app's seed data follows, not something the backend schema enforces.
export interface PracticeCategory {
  slug: string;
  key: string | null;
  label: string;
  kind: "skill_list" | "conjugation_drill";
}

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

export interface DeckUpdatePayload {
  name?: string;
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

export interface SkillIntroExample {
  target_text: string;
  base_text: string;
}

export interface SkillIntroContent {
  explanation: string;
  examples: SkillIntroExample[];
}

export interface Skill {
  id: string;
  course_id: string;
  name: string;
  slug: string;
  order_index: number;
  prerequisite_skill_id: string | null;
  specialty_module: string | null;
  intro_content: SkillIntroContent | null;
  created_at: string;
}

export interface LessonExercise {
  id: string;
  skill_id: string;
  exercise_type: ExerciseType;
  // Shape varies by exercise_type -- see backend/app/services/exercise_grading.py
  // for the exact per-type prompt/submitted_answer contract.
  prompt: Record<string, unknown>;
  order_index: number;
  specialty_module: string | null;
  created_at: string;
}

export interface UserProgress {
  id: string;
  user_id: string;
  skill_id: string;
  mastery_level: number;
  last_practiced_at: string | null;
  times_correct: number;
  times_attempted: number;
  streak_count: number;
  created_at: string;
}

export interface UserExerciseAttempt {
  id: string;
  user_id: string;
  exercise_id: string;
  submitted_answer: Record<string, unknown>;
  is_correct: boolean | null;
  llm_feedback: string | null;
  attempted_at: string;
}

export interface UserExerciseAttemptSubmitPayload {
  user_id: string;
  submitted_answer: Record<string, unknown>;
}

export interface LessonExerciseAttemptResponse {
  attempt: UserExerciseAttempt;
  progress: UserProgress;
  // Present for TRANSLATION/FILL_IN_BLANK/CONJUGATION, null for
  // MULTIPLE_CHOICE (no single "correct answer" string) and FREE_TEXT
  // (not graded here). Sent unconditionally, not just when wrong --
  // callers decide when to display it.
  correct_answer: string | null;
}
