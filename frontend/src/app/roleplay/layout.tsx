"use client";

import type { ReactNode } from "react";
import { CourseSwitcher } from "@/components/course/CourseSwitcher";
import { CourseProvider } from "@/providers/CourseProvider";

// `CourseProvider` re-instantiated here, not shared from the root layout --
// same convention as journal/vocabulary/course/known-vocabulary/paste-in's
// own layout.tsx files, all reading/writing the same `selectedCourseId`
// localStorage key.
export default function RoleplayLayout({ children }: { children: ReactNode }) {
  return (
    <CourseProvider>
      <main className="mx-auto flex min-h-dvh max-w-2xl flex-col gap-6 p-6">
        <div className="flex items-center justify-between">
          <h1 className="font-display text-3xl text-ink">Roleplay</h1>
          <CourseSwitcher />
        </div>
        {children}
      </main>
    </CourseProvider>
  );
}
