// Hand-written to match backend/app/schemas/*.py field-for-field. Not
// generated from the OpenAPI schema -- at this phase's scope (~6 resources)
// reviewing directly against the Pydantic source is faster and easier to
// reason about than wiring in a codegen step. Revisit if the schema surface
// grows a lot.

export type ScriptDirection = "ltr" | "rtl";
export type CardDirection = "target_to_base" | "base_to_target" | "mixed";
export type CardState = "new" | "learning" | "review" | "relearning" | "suspended";
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
  kind: "skill_list" | "conjugation_drill" | "reading_passage";
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
  // null means "use the app-wide default" (15), not "no cap".
  daily_new_card_cap: number | null;
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
  // Populated server-side via selectinload -- null for override-only
  // cards (most of the ones created before the Anki-deck note feature).
  vocabulary_item: VocabularyItem | null;
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
  daily_new_card_cap?: number | null;
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

// Request body for POST /cards/quick-add -- creates one VocabularyItem
// ("note") plus the Card(s) it produces in a single round trip. See
// CardQuickAdd in backend/app/schemas/card.py.
export interface CardQuickAddPayload {
  deck_id: string;
  target_text: string;
  base_text: string;
  part_of_speech?: string | null;
  source?: string | null;
  example_sentence?: string | null;
  example_sentence_translation?: string | null;
  tags?: string[];
  attributes?: Record<string, unknown>;
}

export interface CardQuickAddResponse {
  vocabulary_item: VocabularyItem;
  cards: Card[];
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

export interface VocabularyItem {
  id: string;
  course_id: string;
  // Null means shared curriculum content (lesson-seeded vocab); a real
  // value is a specific user's own word.
  user_id: string | null;
  target_text: string;
  base_text: string;
  part_of_speech: string | null;
  attributes: Record<string, unknown>;
  // Real, sourced content ("where did this word come from") -- distinct
  // from VocabularyExample below (LLM-generated, no provenance). Null for
  // lesson-seeded vocab (Greetings, Family, ...), which has none of this.
  source: string | null;
  example_sentence: string | null;
  example_sentence_translation: string | null;
  tags: string[];
  created_at: string;
}

// Language.grammar_config.vocab_deck -- read via a loose cast where
// consumed (grammar_config itself stays a flexible bag, not fully typed),
// same convention as PracticeCategory above. Absent, or
// dual_direction_cards: false, means "one card per note" -- most
// languages, where reading/producing the script isn't a distinct skill.
export interface VocabDeckConfig {
  dual_direction_cards?: boolean;
  needs_transliteration?: boolean;
  transliteration_label?: string;
  production_gate?: {
    min_successful_recognition_reviews?: number;
    min_days_since_note_added?: number;
  };
}

export interface VocabularyExample {
  id: string;
  target_text: string;
  base_text: string;
  mnemonic: string | null;
  created_at: string;
}

export interface Correction {
  original: string;
  corrected: string;
  explanation: string;
}

export interface VocabSuggestion {
  target_text: string;
  base_text: string;
  example_sentence: string;
}

export interface JournalEntry {
  id: string;
  user_id: string;
  course_id: string;
  submitted_text: string;
  corrected_text: string;
  overall_feedback: string;
  corrections: Correction[];
  vocabulary_suggestions: VocabSuggestion[];
  created_at: string;
}

export interface JournalEntrySubmitPayload {
  user_id: string;
  course_id: string;
  text: string;
}

export interface NewVocabularyWord {
  target_text: string;
  base_text: string;
}

// Client-facing shape only -- the backend's stored `reference_answer` per
// question is never sent to the frontend (see ReadingPassageQuestion in
// backend/app/schemas/reading_passage.py).
export interface ReadingPassageQuestion {
  question_text: string;
}

export interface ReadingPassage {
  id: string;
  course_id: string;
  user_id: string;
  target_text: string;
  base_text: string;
  new_vocabulary: NewVocabularyWord[];
  questions: ReadingPassageQuestion[];
  created_at: string;
}

export interface ReadingPassageGeneratePayload {
  course_id: string;
  user_id: string;
}

export interface ReadingPassageAttemptSubmitPayload {
  user_id: string;
  question_index: number;
  submitted_answer: string;
}

export interface ReadingPassageAttempt {
  id: string;
  user_id: string;
  reading_passage_id: string;
  question_index: number;
  submitted_answer: string;
  is_correct: boolean | null;
  llm_feedback: string | null;
  created_at: string;
}

export type KnownVocabularySource = "placement_check" | "manual" | "promoted";

export interface KnownVocabularyItem {
  id: string;
  course_id: string;
  user_id: string;
  target_text: string;
  source: KnownVocabularySource;
  created_at: string;
}

export interface KnownVocabularyItemCreatePayload {
  course_id: string;
  user_id: string;
  target_text: string;
}

export interface KnownVocabularyBulkCreatePayload {
  course_id: string;
  user_id: string;
  target_texts: string[];
}

export interface KnownVocabularyBulkCreateResponse {
  inserted_count: number;
}

export interface KnownVocabularyPromotePayload {
  deck_id: string;
}

export interface KnownVocabularyFullSetResponse {
  words: string[];
}

export interface PasteInSegment {
  text: string;
  is_word: boolean;
  // Only meaningful when is_word is true.
  is_known: boolean;
}

export interface PasteInAnalyzeResponse {
  segments: PasteInSegment[];
  unknown_words: string[];
}

export interface PasteInAnalyzePayload {
  course_id: string;
  user_id: string;
  text: string;
}

export interface PasteInTranslatePayload {
  course_id: string;
  words: string[];
}

export interface PasteInTranslateResponse {
  translations: NewVocabularyWord[];
}

export interface WeakCard {
  vocabulary_item_id: string;
  target_text: string;
  base_text: string;
  deck_id: string;
  deck_name: string;
  lapses: number;
}

export interface WeakLessonWord {
  vocabulary_item_id: string;
  target_text: string;
  base_text: string;
  skill_id: string;
  skill_name: string;
  accuracy: number;
  times_attempted: number;
}

export interface WeakSkill {
  skill_id: string;
  skill_name: string;
  mastery_level: number;
  times_attempted: number;
}

export interface WeakPointsResponse {
  weak_cards: WeakCard[];
  weak_lesson_words: WeakLessonWord[];
  weak_skills: WeakSkill[];
}

export interface RoleplayScenario {
  id: string;
  name: string;
  slug: string;
  setup_prompt: string;
  order_index: number;
  created_at: string;
}

export type MessageRole = "user" | "assistant";

export interface ConversationMessage {
  id: string;
  conversation_id: string;
  role: MessageRole;
  text: string;
  corrections: Correction[] | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  course_id: string;
  scenario_id: string;
  created_at: string;
}

export interface ConversationStartPayload {
  user_id: string;
  course_id: string;
  scenario_id: string;
}

export interface ConversationStartResponse {
  conversation: Conversation;
  messages: ConversationMessage[];
}

export interface MessageSubmitResponse {
  user_message: ConversationMessage;
  assistant_message: ConversationMessage;
}
