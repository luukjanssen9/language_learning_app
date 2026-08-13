import Link from "next/link";
import type { Skill, UserProgress } from "@/lib/api/types";

interface SkillNodeProps {
  skill: Skill;
  progress: UserProgress | undefined;
}

export function SkillNode({ skill, progress }: SkillNodeProps) {
  const masteryPct = Math.round((progress?.mastery_level ?? 0) * 100);

  return (
    <div className="flex items-center justify-between gap-4 border border-line bg-surface p-4">
      <div className="min-w-0 flex-1">
        <p className="font-display text-lg text-ink">{skill.name}</p>
        <div className="mt-3 h-1 w-full max-w-48 rounded-full bg-line">
          <div
            className="h-full rounded-full bg-accent transition-all"
            style={{ width: `${masteryPct}%` }}
          />
        </div>
        <p className="mt-2 text-xs text-ink-soft">
          {progress ? `${progress.times_correct}/${progress.times_attempted} correct` : "Not started"}
        </p>
      </div>
      <Link
        href={`/skills/${skill.id}/lesson`}
        className="shrink-0 rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-bg"
      >
        Practice
      </Link>
    </div>
  );
}
