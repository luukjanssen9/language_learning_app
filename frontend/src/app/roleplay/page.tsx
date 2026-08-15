"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  useConversations,
  useRoleplayScenarios,
  useStartConversation,
} from "@/hooks/useRoleplay";
import { useBootstrapContext } from "@/providers/BootstrapProvider";
import { useCourseContext } from "@/providers/CourseProvider";

export default function RoleplayPage() {
  const router = useRouter();
  const { userId } = useBootstrapContext();
  const { selectedCourseId } = useCourseContext();
  const { data: scenarios = [] } = useRoleplayScenarios();
  const { data: conversations = [], isPending } = useConversations(userId, selectedCourseId);
  const startConversation = useStartConversation();
  const [startingScenarioId, setStartingScenarioId] = useState<string | null>(null);

  async function handleStart(scenarioId: string) {
    setStartingScenarioId(scenarioId);
    try {
      const result = await startConversation.mutateAsync({
        user_id: userId,
        course_id: selectedCourseId,
        scenario_id: scenarioId,
      });
      router.push(`/roleplay/${result.conversation.id}`);
    } finally {
      setStartingScenarioId(null);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-3">
        <h2 className="text-xs font-medium uppercase tracking-wide text-ink-soft">
          Start a new conversation
        </h2>
        {scenarios.map((scenario) => (
          <button
            key={scenario.id}
            type="button"
            onClick={() => handleStart(scenario.id)}
            disabled={startConversation.isPending}
            className="block border border-line bg-surface p-4 text-left disabled:opacity-50"
          >
            <p className="font-display text-lg text-ink">
              {startingScenarioId === scenario.id ? "Starting…" : scenario.name}
            </p>
          </button>
        ))}
        {scenarios.length === 0 && (
          <p className="text-ink-soft">No scenarios yet — run the seed script.</p>
        )}
      </section>

      {conversations.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-xs font-medium uppercase tracking-wide text-ink-soft">
            Continue a conversation
          </h2>
          <ul className="flex flex-col gap-2">
            {conversations.map((conversation) => {
              const scenario = scenarios.find((s) => s.id === conversation.scenario_id);
              return (
                <li key={conversation.id}>
                  <Link
                    href={`/roleplay/${conversation.id}`}
                    className="block border border-line bg-surface p-4 text-ink underline"
                  >
                    {scenario?.name ?? "Conversation"}
                  </Link>
                </li>
              );
            })}
          </ul>
        </section>
      )}
      {!isPending && conversations.length === 0 && (
        <p className="text-ink-soft">No past conversations yet.</p>
      )}
    </div>
  );
}
