"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { SkillNode } from "@/components/course/SkillNode";
import { useLessonExercises } from "@/hooks/useLessonExercises";
import { useGenerateReadingPassage, useReadingPassages } from "@/hooks/useReadingPassages";
import { useSkills } from "@/hooks/useSkills";
import { useUserProgress } from "@/hooks/useUserProgress";
import { listTenseMoodOptions } from "@/lib/practiceCategories";
import { useBootstrapContext } from "@/providers/BootstrapProvider";
import { useCourseContext } from "@/providers/CourseProvider";

export default function CategoryPage() {
  const { categoryKey } = useParams<{ categoryKey: string }>();
  const { userId } = useBootstrapContext();
  const { practiceCategories, selectedCourseId } = useCourseContext();

  const category = practiceCategories.find((c) => c.slug === categoryKey);

  const { data: skills = [] } = useSkills(selectedCourseId);
  const { data: progress = [] } = useUserProgress(userId);
  const progressBySkillId = new Map(progress.map((p) => [p.skill_id, p]));
  const matchingSkills = skills
    .filter((s) => s.specialty_module === category?.key)
    .sort((a, b) => a.order_index - b.order_index);

  // Only relevant for kind === "conjugation_drill", where matchingSkills
  // is expected to contain exactly one skill -- guarded via `enabled` so
  // this doesn't fire for the (much more common) skill_list categories.
  const conjugationSkillId =
    category?.kind === "conjugation_drill" ? matchingSkills[0]?.id : undefined;
  const { data: exercises = [] } = useLessonExercises(conjugationSkillId ?? "", {
    enabled: Boolean(conjugationSkillId),
  });
  const tenseMoodOptions = conjugationSkillId ? listTenseMoodOptions(exercises) : [];

  const { data: passages = [] } = useReadingPassages(selectedCourseId, userId);
  const generatePassage = useGenerateReadingPassage();

  if (!category) {
    return <p className="text-ink-soft">Category not found.</p>;
  }

  return (
    <div className="flex flex-col gap-4">
      <Link href="/course" className="text-sm text-ink-soft">
        ← Categories
      </Link>
      <h2 className="font-display text-2xl text-ink">{category.label}</h2>

      {category.kind === "skill_list" && (
        <section className="flex flex-col gap-3">
          {matchingSkills.map((skill) => (
            <SkillNode key={skill.id} skill={skill} progress={progressBySkillId.get(skill.id)} />
          ))}
          {matchingSkills.length === 0 && <p className="text-ink-soft">No skills yet.</p>}
        </section>
      )}

      {category.kind === "conjugation_drill" && (
        <section className="flex flex-col gap-3">
          {tenseMoodOptions.map((option) => (
            <Link
              key={option.tenseKey}
              href={`/course/category/${categoryKey}/${option.tenseKey}`}
              className="block border border-line bg-surface p-4 text-ink"
            >
              {option.label}
            </Link>
          ))}
          {tenseMoodOptions.length === 0 && <p className="text-ink-soft">No tenses yet.</p>}
        </section>
      )}

      {category.kind === "reading_passage" && (
        <section className="flex flex-col gap-3">
          <button
            type="button"
            onClick={() => generatePassage.mutate({ courseId: selectedCourseId, userId })}
            disabled={generatePassage.isPending}
            className="self-start rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg disabled:opacity-50"
          >
            {generatePassage.isPending ? "Generating…" : "Generate a new passage"}
          </button>
          {generatePassage.isError && (
            <p className="text-sm text-rating-again">Couldn&apos;t generate a passage. Try again.</p>
          )}
          {passages.map((passage) => (
            <Link
              key={passage.id}
              href={`/reading-passages/${passage.id}`}
              className="block border border-line bg-surface p-4 text-ink"
            >
              {passage.target_text.slice(0, 80)}
              {passage.target_text.length > 80 ? "…" : ""}
            </Link>
          ))}
          {passages.length === 0 && (
            <p className="text-ink-soft">No passages yet — generate your first one above.</p>
          )}
        </section>
      )}
    </div>
  );
}
