"use client";

import type { ReviewRating } from "@/lib/api/types";

const RATINGS: { rating: ReviewRating; label: string; shortcut: string; colorClass: string }[] = [
  { rating: "again", label: "Again", shortcut: "1", colorClass: "bg-rating-again" },
  { rating: "hard", label: "Hard", shortcut: "2", colorClass: "bg-rating-hard" },
  { rating: "good", label: "Good", shortcut: "3", colorClass: "bg-rating-good" },
  { rating: "easy", label: "Easy", shortcut: "4", colorClass: "bg-rating-easy" },
];

export function RatingButtons({
  disabled,
  onRate,
}: {
  disabled: boolean;
  onRate: (rating: ReviewRating) => void;
}) {
  return (
    <div className="grid grid-cols-4 gap-2">
      {RATINGS.map(({ rating, label, shortcut, colorClass }) => (
        <button
          key={rating}
          type="button"
          disabled={disabled}
          onClick={() => onRate(rating)}
          className={`${colorClass} rounded-lg py-3 text-sm font-medium text-bg transition-opacity disabled:opacity-40`}
        >
          {label}
          <span className="block text-xs opacity-75">{shortcut}</span>
        </button>
      ))}
    </div>
  );
}
