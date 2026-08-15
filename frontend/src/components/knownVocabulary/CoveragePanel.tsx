"use client";

import Link from "next/link";
import { useState } from "react";
import type { BandCoverage } from "@/lib/coverageAnalysis";

const GAP_WORDS_DISPLAY_CAP = 30;
// Keeps the review link's URL a sane length and one paste-in review pass
// a reasonable size -- same first-pass-budget heuristic as the placement
// check's ~30-item budget and passage generation's word-sampling cap.
// Band words are already frequency/HSK-ranked, so the first N gap words
// are the most useful subset, not an arbitrary slice.
const REVIEW_WORDS_CAP = 25;

export function CoveragePanel({ coverage }: { coverage: BandCoverage[] }) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const totalWords = coverage.reduce((sum, b) => sum + b.totalWords, 0);
  const totalKnown = coverage.reduce((sum, b) => sum + b.knownCount, 0);
  const overallCoverage = totalWords === 0 ? 0 : totalKnown / totalWords;

  return (
    <div className="flex flex-col gap-3 border border-line bg-surface p-4">
      <p className="text-sm text-ink">
        {totalKnown} / {totalWords} words covered ({Math.round(overallCoverage * 100)}%) across the
        top {totalWords} words.
      </p>
      <ul className="flex flex-col gap-2">
        {coverage.map((band) => {
          const expanded = expandedIndex === band.index;
          const reviewWords = band.gapWords.slice(0, REVIEW_WORDS_CAP);
          return (
            <li key={band.index} className="flex flex-col gap-1.5">
              <button
                type="button"
                onClick={() => setExpandedIndex(expanded ? null : band.index)}
                className="flex items-center justify-between gap-3 text-left text-sm text-ink"
              >
                <span>{band.label}</span>
                <span className="text-ink-soft">
                  {band.knownCount}/{band.totalWords} ({Math.round(band.coverage * 100)}%)
                </span>
              </button>
              <div className="h-1 w-full rounded-full bg-line">
                <div
                  className="h-full rounded-full bg-accent transition-all"
                  style={{ width: `${band.coverage * 100}%` }}
                />
              </div>
              {expanded && (
                <div className="flex flex-col gap-2 pt-1">
                  {band.gapWords.length === 0 ? (
                    <p className="text-xs text-ink-soft">Nothing missing in this band.</p>
                  ) : (
                    <>
                      <p className="text-xs text-ink-soft">
                        {band.gapWords.slice(0, GAP_WORDS_DISPLAY_CAP).join(", ")}
                        {band.gapWords.length > GAP_WORDS_DISPLAY_CAP &&
                          ` … ${band.gapWords.length - GAP_WORDS_DISPLAY_CAP} more — not all shown`}
                      </p>
                      <Link
                        href={`/paste-in?text=${encodeURIComponent(reviewWords.join(" "))}`}
                        className="self-start text-xs font-medium text-ink underline"
                      >
                        Review these words
                      </Link>
                    </>
                  )}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
