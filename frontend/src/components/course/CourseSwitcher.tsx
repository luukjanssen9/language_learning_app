"use client";

import { usePathname, useRouter } from "next/navigation";
import type { ChangeEvent } from "react";
import { useCourseContext } from "@/providers/CourseProvider";

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
    // root rather than always "/course". This switcher is shared by every
    // section that wraps itself in CourseProvider (course, vocabulary,
    // known-vocabulary, ...), so "current section" is read from the URL
    // rather than hardcoded -- found live: hardcoding "/course" here
    // bounced the vocabulary page back to /course on every switch, which
    // was never the intent.
    const section = pathname.startsWith("/vocabulary")
      ? "/vocabulary"
      : pathname.startsWith("/known-vocabulary")
        ? "/known-vocabulary"
        : "/course";
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
