"use client";

import { VocabularyItemRow } from "@/components/vocabulary/VocabularyItemRow";
import { useVocabularyItems } from "@/hooks/useVocabulary";
import { useCourseContext } from "@/providers/CourseProvider";

export default function VocabularyPage() {
  const { selectedCourseId } = useCourseContext();
  const { data: items = [], isPending } = useVocabularyItems(selectedCourseId);

  return (
    <section className="flex flex-col gap-3">
      {items.map((item) => (
        <VocabularyItemRow key={item.id} item={item} />
      ))}
      {!isPending && items.length === 0 && (
        <p className="text-ink-soft">No vocabulary yet — run the seed script.</p>
      )}
    </section>
  );
}
