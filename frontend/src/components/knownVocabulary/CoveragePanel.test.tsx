import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { BandCoverage } from "@/lib/coverageAnalysis";
import { CoveragePanel } from "./CoveragePanel";

function makeBand(overrides: Partial<BandCoverage>): BandCoverage {
  return {
    index: 0,
    label: "Band 0",
    totalWords: 400,
    knownCount: 200,
    coverage: 0.5,
    gapWords: [],
    ...overrides,
  };
}

describe("CoveragePanel", () => {
  it("renders the aggregate stat across all bands", () => {
    const coverage = [
      makeBand({ index: 0, totalWords: 400, knownCount: 400, coverage: 1 }),
      makeBand({ index: 1, totalWords: 400, knownCount: 100, coverage: 0.25 }),
    ];
    render(<CoveragePanel coverage={coverage} />);

    expect(screen.getByText(/500 \/ 800 words covered \(63%\)/)).toBeInTheDocument();
  });

  it("renders each band's own stat and label", () => {
    const coverage = [makeBand({ label: "Band 3", knownCount: 300, totalWords: 400, coverage: 0.75 })];
    render(<CoveragePanel coverage={coverage} />);

    expect(screen.getByText("Band 3")).toBeInTheDocument();
    expect(screen.getByText("300/400 (75%)")).toBeInTheDocument();
  });

  it("hides gap words and the review link until a band is expanded", () => {
    const coverage = [makeBand({ gapWords: ["hola", "adios"] })];
    render(<CoveragePanel coverage={coverage} />);

    expect(screen.queryByText(/hola/)).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Review these words" })).not.toBeInTheDocument();
  });

  it("reveals gap words and a review link when a band is expanded", async () => {
    const user = userEvent.setup();
    const coverage = [makeBand({ label: "Band 5", gapWords: ["hola", "adios"] })];
    render(<CoveragePanel coverage={coverage} />);

    await user.click(screen.getByText("Band 5"));

    expect(screen.getByText("hola, adios")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Review these words" })).toBeInTheDocument();
  });

  it("does not show a review link for a band with no gap words", async () => {
    const user = userEvent.setup();
    const coverage = [makeBand({ label: "Band 9", gapWords: [] })];
    render(<CoveragePanel coverage={coverage} />);

    await user.click(screen.getByText("Band 9"));

    expect(screen.getByText("Nothing missing in this band.")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Review these words" })).not.toBeInTheDocument();
  });

  it("builds the review link with the gap words, capped and URL-encoded", async () => {
    const user = userEvent.setup();
    const manyGapWords = Array.from({ length: 30 }, (_, i) => `palabra${i}`);
    const coverage = [makeBand({ label: "Band 7", gapWords: manyGapWords })];
    render(<CoveragePanel coverage={coverage} />);

    await user.click(screen.getByText("Band 7"));

    const link = screen.getByRole("link", { name: "Review these words" });
    const href = link.getAttribute("href")!;
    const encodedText = href.split("text=")[1];
    const words = decodeURIComponent(encodedText).split(" ");

    expect(words).toHaveLength(25); // capped, not all 30
    expect(words[0]).toBe("palabra0");
    expect(words[24]).toBe("palabra24");
  });

  it("caps the displayed gap-word list and notes how many more exist", async () => {
    const user = userEvent.setup();
    const manyGapWords = Array.from({ length: 35 }, (_, i) => `palabra${i}`);
    const coverage = [makeBand({ gapWords: manyGapWords })];
    render(<CoveragePanel coverage={coverage} />);

    await user.click(screen.getByText("Band 0"));

    expect(screen.getByText(/5 more — not all shown/)).toBeInTheDocument();
  });
});
