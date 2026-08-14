"use client";

import type { ReactNode } from "react";
import { CourseSwitcher } from "@/components/course/CourseSwitcher";
import { CourseProvider } from "@/providers/CourseProvider";

// `CourseProvider` is deliberately re-instantiated here rather than moved
// to the root layout: it's scoped per top-level section the same way
// `course/layout.tsx` already scopes it, and both instances read/write
// the same `selectedCourseId` localStorage key, so a course chosen here
// or on /course stays selected when switching between them.
export default function VocabularyLayout({ children }: { children: ReactNode }) {
  return (
    <CourseProvider>
      <main className="mx-auto flex min-h-dvh max-w-2xl flex-col gap-6 p-6">
        <div className="flex items-center justify-between">
          <h1 className="font-display text-3xl text-ink">Vocabulary</h1>
          <CourseSwitcher />
        </div>
        {children}
      </main>
    </CourseProvider>
  );
}
