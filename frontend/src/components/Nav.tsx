"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Decks" },
  { href: "/course", label: "Course" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <nav className="flex gap-4 border-b border-line px-6 py-3 text-sm">
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
    </nav>
  );
}
