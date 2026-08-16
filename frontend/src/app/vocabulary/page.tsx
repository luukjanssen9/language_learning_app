"use client";

import { VocabularyItemRow } from "@/components/vocabulary/VocabularyItemRow";
import { useVocabularyItems } from "@/hooks/useVocabulary";
import { useBootstrapContext } from "@/providers/BootstrapProvider";
import { useCourseContext } from "@/providers/CourseProvider";

export default function VocabularyPage() {
  const { userId } = useBootstrapContext();
  const { selectedCourseId, selectedTargetLanguage } = useCourseContext();
  const { data: items = [], isPending } = useVocabularyItems(selectedCourseId, userId);
  const hasTts = Boolean(selectedTargetLanguage?.grammar_config.tts);

  return (
    <section className="flex flex-col gap-3">
      {items.map((item) => (
        <VocabularyItemRow key={item.id} item={item} hasTts={hasTts} />
      ))}
      {!isPending && items.length === 0 && (
        <p className="text-ink-soft">No vocabulary yet — run the seed script.</p>
      )}
    </section>
  );
}
