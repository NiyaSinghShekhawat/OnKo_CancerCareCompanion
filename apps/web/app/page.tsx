import Link from "next/link";

const roles = [
  { href: "/doctor", name: "Doctor", note: "Attention queue, Patient 360, Care Plan Copilot" },
  { href: "/patient", name: "Patient", note: "Care journey, today's checklist, SOS" },
  { href: "/caregiver", name: "Caregiver", note: "Permitted view of the journey" },
];

export default function Home() {
  return (
    <main className="max-w-3xl mx-auto px-6 py-16">
      <h1 className="text-4xl font-semibold text-onko-teal">OnKo</h1>
      <p className="mt-2 text-lg">The doctor decides the care. OnKo makes sure the journey stays connected.</p>
      <div className="mt-10 grid gap-3">
        {roles.map((r) => (
          <Link key={r.href} href={r.href}
            className="block bg-white border border-onko-line rounded-lg px-5 py-4 hover:border-onko-teal">
            <div className="font-medium">Open as {r.name}</div>
            <div className="text-sm text-onko-ink/70">{r.note}</div>
          </Link>
        ))}
      </div>
    </main>
  );
}
