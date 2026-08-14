"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { QuickAddButton } from "@/components/QuickAddButton";

const LINKS = [
  { href: "/", label: "Decks" },
  { href: "/course", label: "Course" },
  { href: "/vocabulary", label: "Vocabulary" },
  { href: "/journal", label: "Journal" },
];

export function Nav() {
  const pathname = usePathname();
  // Quick-add creates flashcard notes -- only meaningful in the Decks
  // section (dashboard + deck pages), not Course (lesson content, not
  // Anki-style notes) or Vocabulary (its own read-only page). Found live:
  // showing it everywhere was confusing on pages it doesn't apply to.
  const showQuickAdd = pathname === "/" || pathname.startsWith("/decks");

  return (
    <nav className="flex items-center gap-4 border-b border-line px-6 py-3 text-sm">
      {LINKS.map((link) => {
        const active =
          link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
        return (
          <Link
            key={link.href}
            href={link.href}
            className={active ? "font-medium text-ink" : "text-ink-soft"}
          >
            {link.label}
          </Link>
        );
      })}
      {showQuickAdd && (
        <div className="ml-auto">
          <QuickAddButton />
        </div>
      )}
    </nav>
  );
}
