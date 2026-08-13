import type { SkillIntroContent } from "@/lib/api/types";

export function IntroScreen({
  intro,
  onContinue,
}: {
  intro: SkillIntroContent;
  onContinue: () => void;
}) {
  return (
    <div className="flex flex-col gap-6">
      <p className="text-ink">{intro.explanation}</p>
      <ul className="flex flex-col gap-2">
        {intro.examples.map((example, i) => (
          <li key={i} className="border border-line bg-surface px-4 py-3">
            <p className="text-ink">{example.target_text}</p>
            <p className="text-sm text-ink-soft">{example.base_text}</p>
          </li>
        ))}
      </ul>
      <button
        type="button"
        onClick={onContinue}
        className="self-center rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg"
      >
        Got it, let&apos;s practice
      </button>
    </div>
  );
}
