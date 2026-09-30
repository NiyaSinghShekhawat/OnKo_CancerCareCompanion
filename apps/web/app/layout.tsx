import type { Metadata } from "next";
import { Figtree } from "next/font/google";
import "./globals.css";

const body = Figtree({ subsets: ["latin"], variable: "--font-body" });

export const metadata: Metadata = {
  title: "OnKo — Cancer Care Companion",
  description: "The doctor decides the care. OnKo makes sure the journey stays connected.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={body.variable}>
      <body className="font-sans min-h-screen">{children}</body>
    </html>
  );
}
