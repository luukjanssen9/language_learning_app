import { describe, expect, it } from "vitest";
import type { FrequencyBand } from "./frequencyBands";
import {
  answerCurrentWord,
  currentWord,
  estimatedKnownBands,
  startPlacementCheck,
  type PlacementCheckState,
} from "./placementCheck";

function makeBands(count: number, wordsPerBand = 6): FrequencyBand[] {
  return Array.from({ length: count }, (_, i) => ({
    index: i,
    label: `Band ${i}`,
    words: Array.from({ length: wordsPerBand }, (_, w) => `band${i}-word${w}`),
  }));
}

// Drives the check to completion, answering each question according to a
// ground-truth predicate over the band currently being tested -- lets a
// test express "the user knows bands 0-1 but not 2-3" without needing to
// know the exact binary-search path taken to get there.
function runCheck(
  bands: FrequencyBand[],
  knowsBand: (bandIndex: number) => boolean,
  options?: { samplesPerBand?: number; budget?: number },
): PlacementCheckState {
  let state = startPlacementCheck(bands, options);
  while (!state.done) {
    const word = currentWord(state);
    if (word === null) break;
    state = answerCurrentWord(state, knowsBand(state.currentBandIndex));
  }
  return state;
}

describe("placementCheck", () => {
  it("converges to no known bands when every answer is 'don't know'", () => {
    const state = runCheck(makeBands(4), () => false);
    expect(state.done).toBe(true);
    expect(estimatedKnownBands(state)).toEqual([]);
  });

  it("converges to every band known when every answer is 'know it'", () => {
    const bands = makeBands(4);
    const state = runCheck(bands, () => true);
    expect(state.done).toBe(true);
    expect(estimatedKnownBands(state).map((b) => b.index)).toEqual([0, 1, 2, 3]);
  });

  it("finds a middle frontier from mixed responses", () => {
    const bands = makeBands(4);
    const state = runCheck(bands, (bandIndex) => bandIndex <= 1);
    expect(state.done).toBe(true);
    expect(estimatedKnownBands(state).map((b) => b.index)).toEqual([0, 1]);
  });

  it("still returns a usable (conservative) estimate if the budget runs out mid-band", () => {
    // budget exactly matches one band's worth of samples -- exhausts
    // before the first band's majority is ever decided.
    const bands = makeBands(20);
    const state = runCheck(bands, () => true, { samplesPerBand: 3, budget: 3 });
    expect(state.done).toBe(true);
    expect(state.itemsShown).toBe(3);
    expect(estimatedKnownBands(state)).toEqual([]);
  });

  it("samples deterministic words, not random ones, across repeated runs", () => {
    const bands = makeBands(4);
    const firstWords: string[] = [];
    let state = startPlacementCheck(bands);
    while (!state.done) {
      const word = currentWord(state);
      if (word === null) break;
      firstWords.push(word);
      state = answerCurrentWord(state, true);
    }

    const secondWords: string[] = [];
    let repeat = startPlacementCheck(bands);
    while (!repeat.done) {
      const word = currentWord(repeat);
      if (word === null) break;
      secondWords.push(word);
      repeat = answerCurrentWord(repeat, true);
    }

    expect(secondWords).toEqual(firstWords);
  });

  it("handles an empty band list without erroring", () => {
    const state = startPlacementCheck([]);
    expect(state.done).toBe(true);
    expect(currentWord(state)).toBeNull();
    expect(estimatedKnownBands(state)).toEqual([]);
  });
});
