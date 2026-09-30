import Link from "next/link";
import SafetyNote from "./SafetyNote";

const nav = [
  { href: "/doctor", label: "Overview" },
  { href: "/doctor/patients", label: "Patients" },
];

export default function DoctorShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 bg-white border-r border-onko-line p-5 hidden md:block">
        <Link href="/" className="text-xl font-semibold text-onko-teal">OnKo</Link>
        <nav className="mt-8 grid gap-1">
          {nav.map((n) => (
            <Link key={n.href} href={n.href} className="px-3 py-2 rounded-md hover:bg-onko-mint">{n.label}</Link>
          ))}
        </nav>
      </aside>
      <main className="flex-1 px-6 md:px-10 py-8 max-w-6xl">
        {children}
        <SafetyNote />
      </main>
    </div>
  );
}
