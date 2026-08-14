"use client";

import { useRef, useState } from "react";
import { vocabularyApi } from "@/lib/api/vocabulary";

// Lazily constructs the Audio element on first click, not on mount -- no
// request fires just from rendering the button. The first play for a
// given word has real latency (the backend synthesizes + persists on a
// cache miss); every play after that is served from Postgres and, once
// the browser has it, from its own HTTP cache too (the endpoint sets a
// long-lived, immutable Cache-Control header since the audio never
// changes once generated).
export function PlayAudioButton({ vocabularyItemId }: { vocabularyItemId: string }) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);

  function handlePlay() {
    setHasError(false);
    if (!audioRef.current) {
      audioRef.current = new Audio(vocabularyApi.audioUrl(vocabularyItemId));
    }
    setIsLoading(true);
    audioRef.current
      .play()
      .then(() => setIsLoading(false))
      .catch(() => {
        setIsLoading(false);
        setHasError(true);
      });
  }

  return (
    <button
      type="button"
      onClick={handlePlay}
      disabled={isLoading}
      aria-label="Play pronunciation"
      title={hasError ? "Couldn't play audio. Try again." : "Play pronunciation"}
      className="shrink-0 text-lg leading-none disabled:opacity-50"
    >
      {hasError ? "⚠️" : "🔊"}
    </button>
  );
}
