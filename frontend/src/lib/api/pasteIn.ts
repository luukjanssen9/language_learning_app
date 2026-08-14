import { api } from "./client";
import type {
  PasteInAnalyzePayload,
  PasteInAnalyzeResponse,
  PasteInTranslatePayload,
  PasteInTranslateResponse,
} from "./types";

export const pasteInApi = {
  analyze: (payload: PasteInAnalyzePayload) =>
    api.post<PasteInAnalyzeResponse>("/paste-in/analyze", payload),
  translateUnknownWords: (payload: PasteInTranslatePayload) =>
    api.post<PasteInTranslateResponse>("/paste-in/translate-unknown-words", payload),
};
