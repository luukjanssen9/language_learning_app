"use client";

import type { ReactNode } from "react";
import { CourseSwitcher } from "@/components/course/CourseSwitcher";
import { CourseProvider } from "@/providers/CourseProvider";

// Same pattern as vocabulary/layout.tsx and known-vocabulary/layout.tsx:
// CourseProvider re-instantiated per top-level section, all reading/
// writing the same selectedCourseId localStorage key.
export default function PasteInLayout({ children }: { children: ReactNode }) {
  return (
    <CourseProvider>
      <main className="mx-auto flex min-h-dvh max-w-2xl flex-col gap-6 p-6">
        <div className="flex items-center justify-between">
          <h1 className="font-display text-3xl text-ink">Paste text</h1>
          <CourseSwitcher />
        </div>
        {children}
      </main>
    </CourseProvider>
  );
}
