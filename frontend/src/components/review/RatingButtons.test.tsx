import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { RatingButtons } from "./RatingButtons";

describe("RatingButtons", () => {
  it("renders all four ratings with their labels", () => {
    render(<RatingButtons disabled={false} onRate={() => {}} />);
    expect(screen.getByRole("button", { name: /Again/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Hard/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Good/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Easy/ })).toBeInTheDocument();
  });

  it("disables every button when disabled is true", () => {
    render(<RatingButtons disabled={true} onRate={() => {}} />);
    for (const button of screen.getAllByRole("button")) {
      expect(button).toBeDisabled();
    }
  });

  it("calls onRate with the correct rating when a button is clicked", async () => {
    const onRate = vi.fn();
    const user = userEvent.setup();
    render(<RatingButtons disabled={false} onRate={onRate} />);

    await user.click(screen.getByRole("button", { name: /Good/ }));

    expect(onRate).toHaveBeenCalledTimes(1);
    expect(onRate).toHaveBeenCalledWith("good");
  });
});
