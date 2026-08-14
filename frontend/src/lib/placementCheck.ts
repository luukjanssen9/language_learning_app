import type { FrequencyBand } from "./frequencyBands";

// Binary-search the ordered band list (0 = most frequent/easiest) for the
// "frontier" band -- the boundary past which the user stops reliably
// knowing words. A first-pass heuristic, not empirically tuned: 3 words
// sampled per band tested, capped at a 30-item budget as a safety net
// (in practice, binary search over this app's 7-10 bands converges in
// ~9-15 items, well under that cap -- the cap exists for a much larger
// future band list, not because it's the expected stopping point).
const DEFAULT_SAMPLES_PER_BAND = 3;
const DEFAULT_BUDGET = 30;

export interface PlacementCheckState {
  bands: FrequencyBand[];
  samplesPerBand: number;
  budget: number;
  // Binary-search bounds: bands [0, low-1] are the current known estimate,
  // bands [high+1, bands.length-1] are the current not-known estimate; the
  // search continues within [low, high] until it inverts (low > high).
  low: number;
  high: number;
  currentBandIndex: number;
  currentWords: string[];
  wordIndex: number;
  currentBandKnownCount: number;
  itemsShown: number;
  done: boolean;
}

// Deterministic, not random: evenly-spaced words across the band rather
// than its first N. Keeps the check reproducible/testable and avoids
// always testing the exact same handful of words at a band's frequent
// edge, without needing a seeded RNG threaded through a pure reducer.
function sampleWords(band: FrequencyBand, samplesPerBand: number): string[] {
  const n = band.words.length;
  if (n === 0) return [];
  const count = Math.min(samplesPerBand, n);
  const words: string[] = [];
  for (let i = 0; i < count; i++) {
    const idx = Math.min(Math.floor(((i + 1) * n) / (count + 1)), n - 1);
    words.push(band.words[idx]);
  }
  return words;
}

export function startPlacementCheck(
  bands: FrequencyBand[],
  options: { samplesPerBand?: number; budget?: number } = {},
): PlacementCheckState {
  const samplesPerBand = options.samplesPerBand ?? DEFAULT_SAMPLES_PER_BAND;
  const budget = options.budget ?? DEFAULT_BUDGET;
  const low = 0;
  const high = bands.length - 1;
  const currentBandIndex = Math.floor((low + high) / 2);
  return {
    bands,
    samplesPerBand,
    budget,
    low,
    high,
    currentBandIndex,
    currentWords: bands.length > 0 ? sampleWords(bands[currentBandIndex], samplesPerBand) : [],
    wordIndex: 0,
    currentBandKnownCount: 0,
    itemsShown: 0,
    done: bands.length === 0,
  };
}

export function currentWord(state: PlacementCheckState): string | null {
  if (state.done) return null;
  return state.currentWords[state.wordIndex] ?? null;
}

export function answerCurrentWord(
  state: PlacementCheckState,
  known: boolean,
): PlacementCheckState {
  if (state.done) return state;

  const itemsShown = state.itemsShown + 1;
  const currentBandKnownCount = state.currentBandKnownCount + (known ? 1 : 0);
  const wordIndex = state.wordIndex + 1;

  // Budget exhausted mid-band: stop without acting on this band's
  // incomplete answers, so `low`/`high` stay at their last fully-decided
  // values -- a conservative but still usable estimate.
  if (itemsShown >= state.budget) {
    return { ...state, itemsShown, currentBandKnownCount, wordIndex, done: true };
  }

  if (wordIndex < state.currentWords.length) {
    return { ...state, itemsShown, currentBandKnownCount, wordIndex };
  }

  const majorityKnown = currentBandKnownCount * 2 >= state.currentWords.length;
  const low = majorityKnown ? state.currentBandIndex + 1 : state.low;
  const high = majorityKnown ? state.high : state.currentBandIndex - 1;

  if (low > high) {
    return { ...state, itemsShown, low, high, done: true };
  }

  const nextBandIndex = Math.floor((low + high) / 2);
  return {
    ...state,
    itemsShown,
    low,
    high,
    currentBandIndex: nextBandIndex,
    currentWords: sampleWords(state.bands[nextBandIndex], state.samplesPerBand),
    wordIndex: 0,
    currentBandKnownCount: 0,
  };
}

// Valid at any point, not just once `done` -- reflects the current
// estimate given whatever's been decided so far.
export function estimatedKnownBands(state: PlacementCheckState): FrequencyBand[] {
  return state.bands.slice(0, state.low);
}
