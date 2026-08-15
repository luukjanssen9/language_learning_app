import type { ConversationMessage } from "@/lib/api/types";

export function MessageBubble({ message }: { message: ConversationMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex flex-col gap-1.5 ${isUser ? "items-end" : "items-start"}`}>
      <div
        className={`max-w-[80%] rounded-md border border-line px-3 py-2 text-sm text-ink ${
          isUser ? "bg-accent/10" : "bg-surface"
        }`}
      >
        {message.text}
      </div>

      {message.corrections && message.corrections.length > 0 && (
        <div className="flex max-w-[80%] flex-col gap-1 px-1">
          <h3 className="text-xs font-medium uppercase tracking-wide text-ink-soft">
            Corrections
          </h3>
          <ul className="flex flex-col gap-1">
            {message.corrections.map((c, i) => (
              <li key={i} className="text-xs">
                <span className="text-rating-again line-through">{c.original}</span>{" "}
                <span className="text-rating-good">{c.corrected}</span>
                <p className="text-ink-soft">{c.explanation}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
