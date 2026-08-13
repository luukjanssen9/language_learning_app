import type { LessonExercise } from "./api/types";

export interface TenseMoodOption {
  /** URL segment for /course/category/[categoryKey]/[tenseKey]. */
  tenseKey: string;
  tense: string;
  mood: string;
  label: string;
}

const TENSE_MOOD_LABELS: Record<string, string> = {
  "present-indicative": "Present",
  "preterite-indicative": "Preterite",
  "imperfect-indicative": "Imperfect",
  "future-indicative": "Future",
  "present-subjunctive": "Present Subjunctive",
  "present_perfect-indicative": "Present Perfect",
};

/** Distinct tense/mood combos present in a conjugation skill's exercises,
 * in first-seen order -- the seed script's generator loop always visits
 * tense/mood combos in the same fixed order for its first verb, so this
 * naturally comes out as Present, Preterite, Imperfect, Future, Present
 * Subjunctive, Present Perfect rather than needing a separate sort. */
export function listTenseMoodOptions(exercises: LessonExercise[]): TenseMoodOption[] {
  const seen = new Map<string, TenseMoodOption>();
  for (const exercise of exercises) {
    const tense = String(exercise.prompt.tense);
    const mood = String(exercise.prompt.mood);
    const tenseKey = `${tense}-${mood}`;
    if (!seen.has(tenseKey)) {
      seen.set(tenseKey, {
        tenseKey,
        tense,
        mood,
        label: TENSE_MOOD_LABELS[tenseKey] ?? `${tense} (${mood})`,
      });
    }
  }
  return [...seen.values()];
}

export interface VerbGroup {
  infinitive: string;
  exercisesByPronoun: Record<string, LessonExercise>;
}

/** Groups a conjugation skill's exercises by infinitive, for one chosen
 * tense/mood -- each group is one verb's full 6-person paradigm for that
 * tense, which the drill picks one of at random.
 */
export function groupByVerb(
  exercises: LessonExercise[],
  tense: string,
  mood: string,
): VerbGroup[] {
  const byInfinitive = new Map<string, Record<string, LessonExercise>>();
  for (const exercise of exercises) {
    if (String(exercise.prompt.tense) !== tense || String(exercise.prompt.mood) !== mood) {
      continue;
    }
    const infinitive = String(exercise.prompt.infinitive);
    const pronoun = String(exercise.prompt.pronoun);
    const existing = byInfinitive.get(infinitive) ?? {};
    existing[pronoun] = exercise;
    byInfinitive.set(infinitive, existing);
  }
  return [...byInfinitive.entries()].map(([infinitive, exercisesByPronoun]) => ({
    infinitive,
    exercisesByPronoun,
  }));
}
