"use client";

import { usePathname, useRouter } from "next/navigation";
import type { ChangeEvent } from "react";
import { useCourseContext } from "@/providers/CourseProvider";

// Every top-level section that wraps itself in CourseProvider and renders
// this switcher needs its own entry here -- "/course" is the fallback for
// anything not listed, not a real default. Grown as a plain list rather
// than a nested ternary: found live twice now that a section using this
// switcher without an entry here silently bounces to "/course" on
// switch (first for /vocabulary, then for /known-vocabulary) -- adding
// /journal here now too, the same gap, caught while wiring up /paste-in
// rather than by another live report.
const SWITCHER_SECTIONS = ["/vocabulary", "/known-vocabulary", "/journal", "/paste-in"];

// Shows just the one real course today (only English -> Spanish exists),
// but reads generically from the courses list rather than hardcoding it --
// a second course later needs zero changes here, just a new Course row.
export function CourseSwitcher() {
  const router = useRouter();
  const pathname = usePathname();
  const { courses, languages, selectedCourseId, setSelectedCourseId } = useCourseContext();

  function labelFor(courseId: string): string {
    const course = courses.find((c) => c.id === courseId);
    const language = languages.find((l) => l.id === course?.target_language_id);
    return language?.name ?? course?.name ?? "Course";
  }

  function handleChange(e: ChangeEvent<HTMLSelectElement>) {
    setSelectedCourseId(e.target.value);
    // A category (or tense) picked under the previous course doesn't mean
    // anything under the new one -- land back on the current section's own
    // root rather than always "/course".
    const section = SWITCHER_SECTIONS.find((s) => pathname.startsWith(s)) ?? "/course";
    router.push(section);
  }

  if (courses.length === 0) return null;

  return (
    <select
      value={selectedCourseId}
      onChange={handleChange}
      className="rounded-md border border-line bg-surface px-3 py-1.5 text-sm text-ink"
    >
      {courses.map((course) => (
        <option key={course.id} value={course.id}>
          {labelFor(course.id)}
        </option>
      ))}
    </select>
  );
}
