"use client";
import { useState } from "react";
import { api } from "@/lib/api";

export default function SOSButton({ patientId }: { patientId: string }) {
  const [sent, setSent] = useState(false);
  return (
    <button
      onClick={async () => { await api.sos(patientId); setSent(true); }}
      className="bg-onko-sos text-white font-medium px-4 py-2 rounded-full disabled:opacity-70"
      disabled={sent}
    >
      {sent ? "SOS sent to your care team" : "SOS — get urgent help"}
    </button>
  );
}
