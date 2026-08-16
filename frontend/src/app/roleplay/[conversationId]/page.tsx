"use client";

import { useParams } from "next/navigation";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { MessageBubble } from "@/components/roleplay/MessageBubble";
import { useConversationMessages, useSendMessage } from "@/hooks/useRoleplay";
import { useBootstrapContext } from "@/providers/BootstrapProvider";

export default function ConversationPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { userId } = useBootstrapContext();
  const { data: messages = [], isPending } = useConversationMessages(conversationId, userId);
  const sendMessage = useSendMessage(conversationId, userId);

  const [text, setText] = useState("");
  // Shown as an extra bubble the instant the form submits, before the
  // round trip (including the LLM call) completes -- otherwise the
  // user's own message wouldn't appear until their reply lands, which
  // reads as broken/laggy for a chat UI. Cleared once the mutation
  // settles, at which point the invalidated `messages` query already
  // contains the real, persisted version of it.
  const [pendingText, setPendingText] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, pendingText]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const toSend = text.trim();
    if (!toSend) return;
    setText("");
    setPendingText(toSend);
    sendMessage.mutate(toSend, { onSettled: () => setPendingText(null) });
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3">
        {isPending && <p className="text-ink-soft">Loading…</p>}
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {pendingText && (
          <MessageBubble
            message={{
              id: "pending",
              conversation_id: conversationId,
              role: "user",
              text: pendingText,
              corrections: null,
              created_at: new Date().toISOString(),
            }}
          />
        )}
        {sendMessage.isPending && <p className="text-sm text-ink-soft">Thinking…</p>}
        {sendMessage.isError && (
          <p className="text-sm text-rating-again">Couldn&apos;t send that. Try again.</p>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type your reply…"
          disabled={sendMessage.isPending}
          className="flex-1 rounded-md border border-line bg-bg px-3 py-2 text-ink"
        />
        <button
          type="submit"
          disabled={sendMessage.isPending || !text.trim()}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
