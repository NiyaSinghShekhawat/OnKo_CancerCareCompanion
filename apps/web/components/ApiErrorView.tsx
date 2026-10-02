"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { CircleAlert, LockKeyhole, RotateCcw, ShieldAlert } from "lucide-react";
import { clearBrowserAccessCode, saveBrowserAccessCode } from "@/lib/access-code";

function statusFrom(error: Error) {
  const match = error.message.match(/\[(401|403)\]/);
  return match ? Number(match[1]) : null;
}

export default function ApiErrorView({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const status = statusFrom(error);
  const accessCodeRequired = status === 401 && /access code required/i.test(error.message);
  const [code, setCode] = useState("");
  const [submitted, setSubmitted] = useState(false);

  function submit(e: FormEvent) {
    e.preventDefault();
    if (!code.trim()) return;
    saveBrowserAccessCode(code.trim());
    setSubmitted(true);
    reset();
  }

  if (accessCodeRequired) {
    return (
      <div className="grid min-h-[70vh] place-items-center bg-[#F4F6F5] p-6">
        <form onSubmit={submit} className="w-full max-w-md rounded-3xl bg-white p-8 shadow-sm">
          <LockKeyhole className="text-onko-teal" size={30} />
          <h1 className="mt-4 text-[24px] font-bold">Enter demo access code</h1>
          <p className="mt-2 text-[14px] leading-6 text-onko-muted">
            This deployment is protected. The code is kept only for this browser session and is sent with OnKo API requests.
          </p>
          <label className="mt-5 block text-[13px] font-semibold">
            Access code
            <input
              autoFocus
              type="password"
              value={code}
              onChange={e => setCode(e.target.value)}
              className="mt-2 w-full rounded-xl border border-onko-line bg-onko-surface p-3 text-[15px] outline-none focus:border-onko-teal"
              placeholder="Enter access code"
            />
          </label>
          <button disabled={!code.trim()} className="onko-button-primary mt-4 w-full disabled:opacity-50">
            {submitted ? "Checking…" : "Continue"}
          </button>
          <p className="mt-3 text-[11px] leading-5 text-onko-muted">
            The code is never hard-coded into the frontend or stored permanently.
          </p>
        </form>
      </div>
    );
  }

  if (status === 401) {
    return (
      <div className="grid min-h-[70vh] place-items-center bg-[#F4F6F5] p-6">
        <div className="w-full max-w-lg rounded-3xl bg-white p-8 text-center shadow-sm">
          <LockKeyhole className="mx-auto text-onko-amber" size={30} />
          <h1 className="mt-4 text-[24px] font-bold">Sign-in details were not accepted</h1>
          <p className="mt-2 text-[14px] leading-6 text-onko-muted">
            The selected demo identity is not recognized by the shared backend.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-2">
            <button onClick={() => { clearBrowserAccessCode(); reset(); }} className="onko-button-secondary">
              Re-enter access code
            </button>
            <Link href="/" className="onko-button-primary">Choose workspace</Link>
          </div>
        </div>
      </div>
    );
  }

  if (status === 403) {
    return (
      <div className="grid min-h-[70vh] place-items-center bg-[#F4F6F5] p-6">
        <div className="w-full max-w-lg rounded-3xl bg-white p-8 text-center shadow-sm">
          <ShieldAlert className="mx-auto text-onko-amber" size={30} />
          <h1 className="mt-4 text-[24px] font-bold">This account does not have access to this view</h1>
          <p className="mt-2 text-[14px] leading-6 text-onko-muted">
            OnKo only shows information allowed for the current patient, caregiver or care-team role.
          </p>
          <Link href="/" className="onko-button-primary mt-5">Choose another workspace</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="grid min-h-[70vh] place-items-center bg-[#F4F6F5] p-6">
      <div className="w-full max-w-lg rounded-3xl bg-white p-8 text-center shadow-sm">
        <CircleAlert className="mx-auto text-onko-amber" size={30} />
        <h1 className="mt-4 text-[24px] font-bold">This view could not be loaded</h1>
        <p className="mt-2 text-[14px] leading-6 text-onko-muted">
          Your recorded data has not been changed. Try loading the view again.
        </p>
        <button onClick={reset} className="onko-button-primary mt-5">
          <RotateCcw size={16} />
          Try again
        </button>
      </div>
    </div>
  );
}
