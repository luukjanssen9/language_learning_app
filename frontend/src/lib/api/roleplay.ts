import { api } from "./client";
import type {
  Conversation,
  ConversationMessage,
  ConversationStartPayload,
  ConversationStartResponse,
  MessageSubmitResponse,
  RoleplayScenario,
} from "./types";

export const roleplayApi = {
  scenarios: () => api.get<RoleplayScenario[]>("/roleplay-scenarios"),
  listConversations: (userId: string, courseId: string) =>
    api.get<Conversation[]>(
      `/conversations?${new URLSearchParams({ user_id: userId, course_id: courseId })}`,
    ),
  startConversation: (payload: ConversationStartPayload) =>
    api.post<ConversationStartResponse>("/conversations", payload),
  messages: (conversationId: string) =>
    api.get<ConversationMessage[]>(`/conversations/${conversationId}/messages`),
  sendMessage: (conversationId: string, text: string) =>
    api.post<MessageSubmitResponse>(`/conversations/${conversationId}/messages`, { text }),
};
