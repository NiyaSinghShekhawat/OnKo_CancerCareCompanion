import Link from "next/link";
import { LockKeyhole, ShieldAlert } from "lucide-react";

export default function AccessDeniedPage({
  searchParams,
}: {
  searchParams?: { status?: string };
}) {
  const unauthorized = searchParams?.status === "401";
  const Icon = unauthorized ? LockKeyhole : ShieldAlert;

  return (
    <main className="grid min-h-screen place-items-center bg-onko-canvas p-6">
      <div className="w-full max-w-lg rounded-3xl border border-onko-line bg-white p-8 text-center shadow-sm">
        <Icon className="mx-auto text-onko-amber" size={32} />
        <h1 className="mt-4 text-[26px] font-bold">
          {unauthorized ? "This demo identity was not accepted" : "This role cannot open this view"}
        </h1>
        <p className="mt-2 text-[14px] leading-6 text-onko-muted">
          {unauthorized
            ? "OnKo only accepts demo users that exist in the shared database. Return to the workspace selector and try again."
            : "Access is role- and consent-limited. No data was changed; this account simply does not have permission for the requested page."}
        </p>
        <Link href="/" className="onko-button-primary mt-5">
          Back to workspace selector
        </Link>
      </div>
    </main>
  );
}
