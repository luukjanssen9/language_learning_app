import type { Metadata } from "next";
import { Fraunces, Hanken_Grotesk } from "next/font/google";
import "./globals.css";
import { Nav } from "@/components/Nav";
import { QueryProvider } from "@/providers/QueryProvider";
import { AuthProvider } from "@/providers/AuthProvider";
import { BootstrapProvider } from "@/providers/BootstrapProvider";

const fraunces = Fraunces({
  subsets: ["latin"],
  weight: ["700"],
  variable: "--font-fraunces",
  display: "swap",
});

const hankenGrotesk = Hanken_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-hanken",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Language App",
  description: "Spaced-repetition flashcards for language learning.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${fraunces.variable} ${hankenGrotesk.variable}`}>
      <body className="bg-bg text-ink font-sans antialiased">
        <QueryProvider>
          <AuthProvider>
            <BootstrapProvider>
              <Nav />
              {children}
            </BootstrapProvider>
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
