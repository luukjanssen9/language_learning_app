"use client";

import { useState } from "react";
import { PlayAudioButton } from "@/components/audio/PlayAudioButton";
import { useVocabularyExamples } from "@/hooks/useVocabulary";
import type { VocabularyItem } from "@/lib/api/types";

export function VocabularyItemRow({
  item,
  hasTts,
}: {
  item: VocabularyItem;
  hasTts: boolean;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const { data: examples, isPending, isError } = useVocabularyExamples(item.id, isExpanded);

  return (
    <div className="border border-line bg-surface px-4 py-3">
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <p className="text-ink">
            {item.target_text} <span className="text-ink-soft">→</span> {item.base_text}
          </p>
          {item.part_of_speech && (
            <p className="mt-0.5 text-xs text-ink-soft">{item.part_of_speech}</p>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-3">
          {hasTts && <PlayAudioButton vocabularyItemId={item.id} />}
          <button
            type="button"
            onClick={() => setIsExpanded((v) => !v)}
            className="text-sm text-ink-soft"
          >
            {isExpanded ? "Hide examples" : "Generate examples"}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="mt-3 flex flex-col gap-2 border-t border-line pt-3">
          {isPending && <p className="text-sm text-ink-soft">Generating examples…</p>}
          {isError && (
            <p className="text-sm text-ink-soft">Couldn&apos;t generate examples. Try again.</p>
          )}
          {examples?.[0]?.mnemonic && (
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-ink-soft">
                Mnemonic
              </p>
              <p className="text-sm text-ink">{examples[0].mnemonic}</p>
            </div>
          )}
          {examples?.map((example) => (
            <div key={example.id} className="text-sm">
              <p className="text-ink">{example.target_text}</p>
              <p className="text-ink-soft">{example.base_text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
