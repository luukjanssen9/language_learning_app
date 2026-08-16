"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { QuickAddButton } from "@/components/QuickAddButton";
import { useAuthContext } from "@/providers/AuthProvider";

const LINKS = [
  { href: "/", label: "Decks" },
  { href: "/course", label: "Course" },
  { href: "/vocabulary", label: "Vocabulary" },
  { href: "/known-vocabulary", label: "Known words" },
  { href: "/journal", label: "Journal" },
  { href: "/paste-in", label: "Paste text" },
  { href: "/roleplay", label: "Roleplay" },
];

export function Nav() {
  const pathname = usePathname();
  const { displayName, logout } = useAuthContext();
  // Quick-add creates flashcard notes -- only meaningful in the Decks
  // section (dashboard + deck pages), not Course (lesson content, not
  // Anki-style notes), Vocabulary (its own read-only page), Known words,
  // or Paste text (both have their own inline add-to-deck action
  // instead). Found live: showing it everywhere was confusing on pages
  // it doesn't apply to.
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
      <div className="ml-auto flex items-center gap-4">
        {showQuickAdd && <QuickAddButton />}
        <div className="flex items-center gap-3 text-ink-soft">
          <span>Signed in as {displayName}</span>
          <button type="button" onClick={() => void logout()} className="underline">
            Log out
          </button>
        </div>
      </div>
    </nav>
  );
}
