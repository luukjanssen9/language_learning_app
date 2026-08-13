"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { ConjugationDrill } from "@/components/course/ConjugationDrill";
import { useLessonExercises } from "@/hooks/useLessonExercises";
import { useSkills } from "@/hooks/useSkills";
import type { LessonExercise } from "@/lib/api/types";
import { groupByVerb, listTenseMoodOptions, type VerbGroup } from "@/lib/practiceCategories";
import { useCourseContext } from "@/providers/CourseProvider";

function pickRandom<T>(items: T[]): T | undefined {
  if (items.length === 0) return undefined;
  return items[Math.floor(Math.random() * items.length)];
}

// A `data: exercises = []` destructuring default creates a brand-new
// array every render while `data` is still undefined (loading) -- fine
// for plain rendering elsewhere in this app, but this page compares
// exercises-derived values by reference to detect real changes, so it
// needs one stable "empty" identity instead of a fresh one each render.
const EMPTY_EXERCISES: LessonExercise[] = [];

export default function ConjugationTensePage() {
  const { categoryKey, tenseKey } = useParams<{ categoryKey: string; tenseKey: string }>();
  const { practiceCategories, selectedCourseId, selectedTargetLanguage } = useCourseContext();

  const category = practiceCategories.find((c) => c.slug === categoryKey);
  // Every seeded language declares its own pronoun_labels in
  // grammar_config.conjugation (2026-08-14 "v1 Dutch course" decision);
  // ConjugationDrill itself falls back to the raw internal key per-slot
  // if a label is ever missing, so `{}` here is a safe worst case, not
  // silently wrong.
  const conjugationConfig = selectedTargetLanguage?.grammar_config.conjugation as
    | { pronoun_labels?: Record<string, string> }
    | undefined;
  const pronounLabels = conjugationConfig?.pronoun_labels ?? {};
  const { data: skills = [] } = useSkills(selectedCourseId);
  const skillId = skills.find((s) => s.specialty_module === category?.key)?.id;

  const { data: rawExercises, isPending } = useLessonExercises(skillId ?? "", {
    enabled: Boolean(skillId),
  });
  const exercises = rawExercises ?? EMPTY_EXERCISES;

  // `options` must itself be memoized on `[exercises]` for `option` below
  // to come out referentially stable across re-renders (Array.find on the
  // same array reference returns the same element reference) -- without
  // this, `option` is a brand-new object every render (a fresh .find()
  // over a freshly-built array), which cascades into `groups` below
  // recomputing every render too, which was triggering the render-time
  // state adjustment on every single render: an infinite re-render loop,
  // caught live rather than by review.
  const options = useMemo(() => listTenseMoodOptions(exercises), [exercises]);
  const option = options.find((o) => o.tenseKey === tenseKey);
  // Pure/deterministic, so a real useMemo -- only recomputes when the
  // fetched exercises or the chosen tense actually change.
  const groups = useMemo(
    () => (option ? groupByVerb(exercises, option.tense, option.mood) : []),
    [exercises, option],
  );

  // Random selection is inherently impure, so it's state, not something
  // to fake through useMemo's dependency list. Picked via React's
  // documented "adjust state during render" pattern (setState called
  // directly in the render body, guarded by comparing against the
  // previous `groups` reference) rather than an effect, since this is
  // deriving state from a prop change, not synchronizing with anything
  // external. "Try another verb" re-picks explicitly via the handler.
  //
  // The initial pick MUST come from a lazy useState initializer, not
  // solely from the groups-changed comparison below: when `exercises` is
  // already cached (the normal case -- the category picker page fetches
  // the same query first), `groups` is already correct on this
  // component's very first render, so `groupsAtLastPick`'s own initial
  // value (also `groups`, from that same first render) starts equal to
  // it -- the comparison never sees a "change" and a pick would never
  // happen at all. Caught live: every tense showed "No verbs yet" when
  // reached via the picker page, despite exercises genuinely being
  // loaded (confirmed by the picker page itself listing tenses from
  // that same data).
  //
  // `pickId` is bumped alongside every pick purely so ConjugationDrill's
  // `key` changes even when the same infinitive is re-picked by chance --
  // without it, re-rolling the same verb wouldn't remount the drill, and
  // its previous answers/results would still be showing.
  const [group, setGroup] = useState<VerbGroup | undefined>(() => pickRandom(groups));
  const [pickId, setPickId] = useState(0);
  const [groupsAtLastPick, setGroupsAtLastPick] = useState(groups);
  if (groups !== groupsAtLastPick) {
    setGroupsAtLastPick(groups);
    setGroup(pickRandom(groups));
    setPickId((n) => n + 1);
  }

  if (isPending) return <p className="text-ink-soft">Loading…</p>;
  if (!category || !option) {
    return <p className="text-ink-soft">Not found.</p>;
  }

  return (
    <div className="flex flex-col gap-4">
      <Link href={`/course/category/${categoryKey}`} className="text-sm text-ink-soft">
        ← {category.label}
      </Link>
      <h2 className="font-display text-2xl text-ink">{option.label}</h2>

      {group ? (
        <ConjugationDrill
          key={pickId}
          verbGroup={group}
          pronounLabels={pronounLabels}
          onTryAnother={() => {
            setGroup(pickRandom(groups));
            setPickId((n) => n + 1);
          }}
        />
      ) : (
        <p className="text-ink-soft">No verbs for this tense yet.</p>
      )}
    </div>
  );
}
