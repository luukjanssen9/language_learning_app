import { useMutation } from "@tanstack/react-query";
import { pasteInApi } from "@/lib/api/pasteIn";
import type { PasteInAnalyzePayload, PasteInTranslatePayload } from "@/lib/api/types";

// Both plain mutations, no query caching -- this tool is ephemeral
// (compute-on-submit), not persisted, so there's nothing to invalidate or
// re-fetch.
export function useAnalyzePasteIn() {
  return useMutation({
    mutationFn: (payload: PasteInAnalyzePayload) => pasteInApi.analyze(payload),
  });
}

export function useTranslateUnknownWords() {
  return useMutation({
    mutationFn: (payload: PasteInTranslatePayload) => pasteInApi.translateUnknownWords(payload),
  });
}
