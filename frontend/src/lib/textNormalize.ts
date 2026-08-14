// Accent- and case-insensitive comparison, mirroring the backend's
// app/services/text_normalize.py (2026-08-14) -- used here to check
// whether a journal vocab suggestion already exists in the course's
// vocabulary before rendering its "Add to deck" button as already-added.
export function normalizeForComparison(text: string): string {
  return text
    .trim()
    .toLowerCase()
    .normalize("NFKD")
    .replace(/\p{Diacritic}/gu, "");
}
