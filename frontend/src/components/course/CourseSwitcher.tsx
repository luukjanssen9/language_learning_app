"use client";

import { useRouter } from "next/navigation";
import type { ChangeEvent } from "react";
import { useCourseContext } from "@/providers/CourseProvider";

// Shows just the one real course today (only English -> Spanish exists),
// but reads generically from the courses list rather than hardcoding it --
// a second course later needs zero changes here, just a new Course row.
export function CourseSwitcher() {
  const router = useRouter();
  const { courses, languages, selectedCourseId, setSelectedCourseId } = useCourseContext();

  function labelFor(courseId: string): string {
    const course = courses.find((c) => c.id === courseId);
    const language = languages.find((l) => l.id === course?.target_language_id);
    return language?.name ?? course?.name ?? "Course";
  }

  function handleChange(e: ChangeEvent<HTMLSelectElement>) {
    setSelectedCourseId(e.target.value);
    // A category picked under the previous course doesn't mean anything
    // under the new one -- always land back on the category picker.
    router.push("/course");
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
