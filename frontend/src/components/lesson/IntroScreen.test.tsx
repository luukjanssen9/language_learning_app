import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { SkillIntroContent } from "@/lib/api/types";
import { IntroScreen } from "./IntroScreen";

function makeIntro(overrides: Partial<SkillIntroContent>): SkillIntroContent {
  return {
    explanation: "Use ser for permanent traits, estar for temporary states.",
    examples: [{ target_text: "Soy alto.", base_text: "I am tall." }],
    ...overrides,
  };
}

describe("IntroScreen", () => {
  it("renders the explanation and every example", () => {
    const intro = makeIntro({
      examples: [
        { target_text: "Soy alto.", base_text: "I am tall." },
        { target_text: "Estoy cansado.", base_text: "I am tired." },
      ],
    });
    render(<IntroScreen intro={intro} onContinue={vi.fn()} />);

    expect(screen.getByText(intro.explanation)).toBeInTheDocument();
    expect(screen.getByText("Soy alto.")).toBeInTheDocument();
    expect(screen.getByText("I am tall.")).toBeInTheDocument();
    expect(screen.getByText("Estoy cansado.")).toBeInTheDocument();
    expect(screen.getByText("I am tired.")).toBeInTheDocument();
  });

  it("calls onContinue when the continue button is clicked", async () => {
    const user = userEvent.setup();
    const onContinue = vi.fn();
    render(<IntroScreen intro={makeIntro({})} onContinue={onContinue} />);

    await user.click(screen.getByRole("button", { name: "Got it, let's practice" }));

    expect(onContinue).toHaveBeenCalledTimes(1);
  });
});
