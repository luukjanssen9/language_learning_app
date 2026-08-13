"use client";

import { useQuery } from "@tanstack/react-query";
import { createContext, useContext, useState, type ReactNode } from "react";
import { coursesApi } from "@/lib/api/courses";
import { languagesApi } from "@/lib/api/languages";
import type { Course, Language, PracticeCategory } from "@/lib/api/types";
import { useBootstrapContext } from "./BootstrapProvider";

const STORAGE_KEY = "language-app:selected-course-id";

interface CourseContextValue {
  courses: Course[];
  languages: Language[];
  selectedCourseId: string;
  setSelectedCourseId: (id: string) => void;
  practiceCategories: PracticeCategory[];
  // The selected course's target Language row -- exposed generally
  // (not just its derived practiceCategories) so other per-language
  // grammar_config content (e.g. the conjugation drill's pronoun
  // labels) has one shared place to read it from, instead of every
  // page re-deriving course -> target language itself.
  selectedTargetLanguage: Language | undefined;
}

const CourseContext = createContext<CourseContextValue | null>(null);

export function useCourseContext(): CourseContextValue {
  const ctx = useContext(CourseContext);
  if (!ctx) {
    throw new Error("useCourseContext must be used within CourseProvider");
  }
  return ctx;
}

// No loading gate needed here the way BootstrapProvider has one -- this
// provider only ever renders nested inside BootstrapProvider's success
// branch, so `courses`/`languages` (both already-seeded via bootstrap.ts)
// resolve near-instantly, and everything below degrades gracefully
// (empty arrays) for the brief moment before that first fetch settles.
export function CourseProvider({ children }: { children: ReactNode }) {
  const { courseId: bootstrapCourseId } = useBootstrapContext();

  const { data: courses = [] } = useQuery({ queryKey: ["courses"], queryFn: coursesApi.list });
  const { data: languages = [] } = useQuery({
    queryKey: ["languages"],
    queryFn: languagesApi.list,
  });

  // Stored as a plain string, not parsed via readBootstrapCache's JSON
  // convention -- this is a single id, not a structured object.
  const [storedCourseId, setStoredCourseId] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(STORAGE_KEY);
  });

  // Self-heals if the stored id no longer matches any fetched course
  // (e.g. the dev DB got reset) -- same class of problem bootstrap.ts's
  // cacheIsStillValid check exists for, falling back to the bootstrap
  // course rather than rendering an empty/broken switcher.
  const selectedCourseId =
    storedCourseId && courses.some((c) => c.id === storedCourseId)
      ? storedCourseId
      : bootstrapCourseId;

  function setSelectedCourseId(id: string) {
    setStoredCourseId(id);
    window.localStorage.setItem(STORAGE_KEY, id);
  }

  const selectedCourse = courses.find((c) => c.id === selectedCourseId);
  const targetLanguage = languages.find((l) => l.id === selectedCourse?.target_language_id);
  const practiceCategories =
    (targetLanguage?.grammar_config.practice_categories as PracticeCategory[] | undefined) ?? [];

  const value: CourseContextValue = {
    courses,
    languages,
    selectedCourseId,
    setSelectedCourseId,
    practiceCategories,
    selectedTargetLanguage: targetLanguage,
  };

  return <CourseContext.Provider value={value}>{children}</CourseContext.Provider>;
}
