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
  messages: (conversationId: string, userId: string) =>
    api.get<ConversationMessage[]>(
      `/conversations/${conversationId}/messages?${new URLSearchParams({ user_id: userId })}`,
    ),
  sendMessage: (conversationId: string, userId: string, text: string) =>
    api.post<MessageSubmitResponse>(`/conversations/${conversationId}/messages`, {
      user_id: userId,
      text,
    }),
};
