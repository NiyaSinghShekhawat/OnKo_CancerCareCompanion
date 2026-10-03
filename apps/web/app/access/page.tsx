"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { LockKeyhole, ShieldCheck } from "lucide-react";
import { saveBrowserAccessCode } from "@/lib/access-code";

export default function AccessPage() {
  const router = useRouter();
  const [code, setCode] = useState("");

  function submit(e: FormEvent) {
    e.preventDefault();
    if (!code.trim()) return;
    saveBrowserAccessCode(code.trim());
    router.push("/");
    router.refresh();
  }

  return (
    <main className="grid min-h-screen place-items-center bg-onko-canvas p-6">
      <form onSubmit={submit} className="w-full max-w-md rounded-3xl border border-onko-line bg-white p-8 shadow-sm">
        <span className="grid h-12 w-12 place-items-center rounded-2xl bg-onko-softteal text-onko-teal">
          <LockKeyhole size={23} />
        </span>
        <p className="onko-eyebrow mt-5">Protected demo</p>
        <h1 className="mt-1 text-[28px] font-bold">Enter OnKo access code</h1>
        <p className="mt-2 text-[14px] leading-6 text-onko-muted">
          This demo environment requires a shared access code before protected data can be loaded.
        </p>

        <label className="mt-6 block text-[13px] font-semibold">
          Access code
          <input
            autoFocus
            type="password"
            autoComplete="off"
            value={code}
            onChange={e => setCode(e.target.value)}
            className="mt-2 w-full rounded-xl border border-onko-line bg-onko-surface p-3 text-[15px] outline-none focus:border-onko-teal"
            placeholder="Enter access code"
          />
        </label>

        <button disabled={!code.trim()} className="onko-button-primary mt-4 w-full disabled:opacity-50">
          Continue to OnKo
        </button>

        <div className="mt-4 flex gap-2 rounded-xl bg-onko-softteal/60 p-3 text-[12px] leading-5 text-onko-muted">
          <ShieldCheck className="mt-0.5 shrink-0 text-onko-teal" size={17} />
          The code is stored only for this browser session and sent as the X-Access-Code header. It is not hard-coded in the app.
        </div>
      </form>
    </main>
  );
}
