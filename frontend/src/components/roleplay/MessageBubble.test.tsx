import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ConversationMessage } from "@/lib/api/types";
import { MessageBubble } from "./MessageBubble";

function makeMessage(overrides: Partial<ConversationMessage>): ConversationMessage {
  return {
    id: "m1",
    conversation_id: "c1",
    role: "assistant",
    text: "¡Hola!",
    corrections: null,
    created_at: "2026-08-15T00:00:00Z",
    ...overrides,
  };
}

describe("MessageBubble", () => {
  it("renders an assistant message's text", () => {
    render(<MessageBubble message={makeMessage({ role: "assistant", text: "¡Bienvenido!" })} />);

    expect(screen.getByText("¡Bienvenido!")).toBeInTheDocument();
  });

  it("renders a user message's text", () => {
    render(<MessageBubble message={makeMessage({ role: "user", text: "Hola, quiero un café" })} />);

    expect(screen.getByText("Hola, quiero un café")).toBeInTheDocument();
  });

  it("does not show a corrections section when there are none", () => {
    render(<MessageBubble message={makeMessage({ role: "user", corrections: [] })} />);

    expect(screen.queryByText("Corrections")).not.toBeInTheDocument();
  });

  it("does not show a corrections section when corrections is null", () => {
    render(<MessageBubble message={makeMessage({ role: "assistant", corrections: null })} />);

    expect(screen.queryByText("Corrections")).not.toBeInTheDocument();
  });

  it("shows corrections with original, corrected, and explanation", () => {
    render(
      <MessageBubble
        message={makeMessage({
          role: "user",
          corrections: [
            { original: "quiero un cafe", corrected: "quiero un café", explanation: "missing accent" },
          ],
        })}
      />,
    );

    expect(screen.getByText("Corrections")).toBeInTheDocument();
    expect(screen.getByText("quiero un cafe")).toBeInTheDocument();
    expect(screen.getByText("quiero un café")).toBeInTheDocument();
    expect(screen.getByText("missing accent")).toBeInTheDocument();
  });
});
