import type { FrequencyBand } from "./frequencyBands";
import { normalizeForComparison } from "./textNormalize";

export interface BandCoverage {
  index: number;
  label: string;
  totalWords: number;
  knownCount: number;
  coverage: number; // 0..1
  // In band order (already frequency/HSK-ranked), not the full band --
  // only the words NOT in the known set.
  gapWords: string[];
}

// Pure, independently testable -- same convention as deckStats.ts/
// sortCards.ts/placementCheck.ts. Normalizes both sides before matching
// (same accent/case-insensitive belt-and-suspenders approach as
// NewVocabularyRow's isAlreadyAdded) rather than trusting either the
// bundled band data or the API response to already be normalized
// consistently.
export function computeCoverage(bands: FrequencyBand[], knownWords: string[]): BandCoverage[] {
  const known = new Set(knownWords.map(normalizeForComparison));
  return bands.map((band) => {
    const gapWords: string[] = [];
    let knownCount = 0;
    for (const word of band.words) {
      if (known.has(normalizeForComparison(word))) {
        knownCount++;
      } else {
        gapWords.push(word);
      }
    }
    return {
      index: band.index,
      label: band.label,
      totalWords: band.words.length,
      knownCount,
      coverage: band.words.length === 0 ? 0 : knownCount / band.words.length,
      gapWords,
    };
  });
}
