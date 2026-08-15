import { describe, expect, it } from "vitest";
import { computeCoverage } from "./coverageAnalysis";
import type { FrequencyBand } from "./frequencyBands";

function makeBand(overrides: Partial<FrequencyBand>): FrequencyBand {
  return {
    index: 0,
    label: "Band",
    words: [],
    ...overrides,
  };
}

describe("computeCoverage", () => {
  it("reports full coverage when every word in a band is known", () => {
    const bands = [makeBand({ words: ["hola", "gato"] })];
    const result = computeCoverage(bands, ["hola", "gato"]);

    expect(result[0].knownCount).toBe(2);
    expect(result[0].totalWords).toBe(2);
    expect(result[0].coverage).toBe(1);
    expect(result[0].gapWords).toEqual([]);
  });

  it("reports zero coverage when no word in a band is known", () => {
    const bands = [makeBand({ words: ["hola", "gato"] })];
    const result = computeCoverage(bands, []);

    expect(result[0].knownCount).toBe(0);
    expect(result[0].coverage).toBe(0);
    expect(result[0].gapWords).toEqual(["hola", "gato"]);
  });

  it("computes partial coverage and preserves band order in gapWords", () => {
    const bands = [makeBand({ words: ["uno", "dos", "tres", "cuatro"] })];
    const result = computeCoverage(bands, ["dos", "cuatro"]);

    expect(result[0].knownCount).toBe(2);
    expect(result[0].coverage).toBeCloseTo(0.5);
    expect(result[0].gapWords).toEqual(["uno", "tres"]);
  });

  it("matches known words accent- and case-insensitively", () => {
    const bands = [makeBand({ words: ["está", "más"] })];
    const result = computeCoverage(bands, ["esta", "MAS"]);

    expect(result[0].knownCount).toBe(2);
    expect(result[0].gapWords).toEqual([]);
  });

  it("handles an empty band without dividing by zero", () => {
    const bands = [makeBand({ words: [] })];
    const result = computeCoverage(bands, ["hola"]);

    expect(result[0].totalWords).toBe(0);
    expect(result[0].coverage).toBe(0);
  });

  it("computes coverage independently per band", () => {
    const bands = [
      makeBand({ index: 0, label: "Band 0", words: ["hola"] }),
      makeBand({ index: 1, label: "Band 1", words: ["adios"] }),
    ];
    const result = computeCoverage(bands, ["hola"]);

    expect(result[0].coverage).toBe(1);
    expect(result[1].coverage).toBe(0);
  });
});
