import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { roleplayApi } from "@/lib/api/roleplay";
import type { ConversationStartPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/queryKeys";

export function useRoleplayScenarios() {
  return useQuery({
    queryKey: queryKeys.roleplayScenarios,
    queryFn: () => roleplayApi.scenarios(),
  });
}

export function useConversations(userId: string, courseId: string) {
  return useQuery({
    queryKey: queryKeys.conversations(userId, courseId),
    queryFn: () => roleplayApi.listConversations(userId, courseId),
    enabled: Boolean(userId && courseId),
  });
}

export function useStartConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ConversationStartPayload) => roleplayApi.startConversation(payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.conversations(data.conversation.user_id, data.conversation.course_id),
      });
    },
  });
}

export function useConversationMessages(conversationId: string, userId: string) {
  return useQuery({
    queryKey: queryKeys.conversationMessages(conversationId),
    queryFn: () => roleplayApi.messages(conversationId, userId),
    enabled: Boolean(conversationId),
  });
}

export function useSendMessage(conversationId: string, userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (text: string) => roleplayApi.sendMessage(conversationId, userId, text),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.conversationMessages(conversationId),
      });
    },
  });
}
