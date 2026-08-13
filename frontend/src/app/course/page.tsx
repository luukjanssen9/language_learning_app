"use client";

import Link from "next/link";
import { useCourseContext } from "@/providers/CourseProvider";

export default function CoursePage() {
  const { practiceCategories } = useCourseContext();

  return (
    <section className="flex flex-col gap-3">
      {practiceCategories.map((category) => (
        <Link
          key={category.slug}
          href={`/course/category/${category.slug}`}
          className="block border border-line bg-surface p-4"
        >
          <p className="font-display text-lg text-ink">{category.label}</p>
        </Link>
      ))}
      {practiceCategories.length === 0 && (
        <p className="text-ink-soft">No practice categories yet — run the seed script.</p>
      )}
    </section>
  );
}
