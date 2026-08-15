import type { VocabularyItem } from "@/lib/api/types";

// Presentational, no hook wiring -- same split as KnownVocabularyRow. No
// Promote button (already has a flashcard) and no Remove button (deleting
// a flashcard is a real, more consequential action that belongs on the
// deck page, not a read-only "here's what you know" row here).
export function MasteredVocabularyRow({ item }: { item: VocabularyItem }) {
  return (
    <li className="flex items-center justify-between gap-3 border-t border-line pt-2 first:border-t-0 first:pt-0">
      <div>
        <p className="text-ink">
          {item.target_text} <span className="text-ink-soft">→</span> {item.base_text}
        </p>
        <p className="text-xs text-ink-soft">Mastered</p>
      </div>
    </li>
  );
}
