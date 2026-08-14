"use client";

import type { ReactNode } from "react";
import { CourseSwitcher } from "@/components/course/CourseSwitcher";
import { CourseProvider } from "@/providers/CourseProvider";

// `CourseProvider` re-instantiated here, not shared from the root layout --
// same convention as vocabulary/layout.tsx and course/layout.tsx, all
// reading/writing the same `selectedCourseId` localStorage key.
export default function JournalLayout({ children }: { children: ReactNode }) {
  return (
    <CourseProvider>
      <main className="mx-auto flex min-h-dvh max-w-2xl flex-col gap-6 p-6">
        <div className="flex items-center justify-between">
          <h1 className="font-display text-3xl text-ink">Journal</h1>
          <CourseSwitcher />
        </div>
        {children}
      </main>
    </CourseProvider>
  );
}
