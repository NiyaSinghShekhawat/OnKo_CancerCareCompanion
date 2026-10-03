"use client";

import { useEffect, useState } from "react";
import { Bell, Globe2, KeyRound, ShieldCheck, UserRound, UsersRound } from "lucide-react";
import type { Caregiver, Patient } from "@/lib/types";
import ABHAConnection from "@/components/ABHAConnection";
import PatientFirstAccess from "@/components/PatientFirstAccess";
import LanguagePreview from "@/components/LanguagePreview";
import CaregiverAccessManager from "@/components/CaregiverAccessManager";

export default function PatientProfileClient({ p, caregivers }: { p: Patient; caregivers: Caregiver[] }) {
  const [language, setLanguage] = useState(p.preferred_language);
  const [whatsapp, setWhatsapp] = useState(true);
  const [saved, setSaved] = useState(false);
  const [patientPassword, setPatientPassword] = useState("");

  useEffect(() => {
    setPatientPassword(window.sessionStorage.getItem("onko-patient-password") || "");
  }, []);

  return (
    <div className="mx-auto max-w-5xl">
      <p className="onko-eyebrow">Profile & access</p>
      <h1 className="mt-1 text-[30px] font-bold sm:text-[38px]">My Care Profile</h1>
      <p className="mt-2 text-[14px] text-onko-muted">
        Caregiver access, consent and communication preferences live here so your main care navigation stays focused.
      </p>

      <section className="onko-card mt-5 p-5">
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-xl bg-onko-softteal text-onko-teal"><UserRound size={20}/></span>
          <div><h2 className="text-[19px] font-bold">{p.name}</h2><p className="text-[13px] text-onko-muted">{p.id} · {p.phone_whatsapp}</p></div>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl bg-onko-surface p-4">
            <p className="text-[11px] font-bold uppercase text-onko-muted">Journey state</p>
            <p className="mt-1 text-[14px] font-bold capitalize">{p.journey_state.replaceAll("_"," ").toLowerCase()}</p>
            <p className="mt-1 text-[12px] text-onko-muted">Chapter {p.journey_chapter}</p>
          </div>
          <div className="rounded-xl bg-onko-surface p-4">
            <p className="text-[11px] font-bold uppercase text-onko-muted">ABHA linkage</p>
            <p className="mt-1 text-[14px] font-bold">{p.abha_id||"Not linked in this prototype"}</p>
            <ABHAConnection abhaId={p.abha_id}/>
            <PatientFirstAccess patient={p}/>
          </div>
        </div>
      </section>

      <section className="onko-card mt-5 p-5">
        <div className="flex items-center gap-3"><UsersRound size={20} className="text-onko-teal"/><h2 className="text-[20px] font-bold">Caregiver & consent</h2></div>
        <div className="mt-3 flex gap-3 rounded-xl bg-onko-softteal/60 p-4 text-[13px] leading-5 text-onko-muted">
          <ShieldCheck size={18} className="shrink-0 text-onko-teal"/>
          Caregiver access is patient-controlled and revocable. Consent and permission changes below are persisted to the shared backend.
        </div>
      </section>

      <CaregiverAccessManager patient={p} initial={caregivers}/>

      <section id="language" className="onko-card mt-5 scroll-mt-28 p-5">
        <div className="flex items-center gap-3"><Globe2 size={20} className="text-onko-teal"/><h2 className="text-[20px] font-bold">Language & communication</h2></div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <label className="text-[13px] font-semibold">Preferred language
            <select value={language} onChange={e=>{setLanguage(e.target.value);setSaved(false)}} className="mt-2 w-full rounded-xl border border-onko-line bg-white p-3 text-[14px]">
              <option>English</option><option>Hindi</option><option>Telugu</option>
            </select>
          </label>
          <div>
            <p className="text-[13px] font-semibold">Daily WhatsApp checklist</p>
            <button onClick={()=>{setWhatsapp(v=>!v);setSaved(false)}} className={"mt-2 flex w-full items-center justify-between rounded-xl border p-3 text-[14px] "+(whatsapp?"border-onko-teal bg-onko-softteal":"border-onko-line bg-white")}>
              <span className="flex items-center gap-2"><Bell size={17}/>{whatsapp?"Enabled":"Disabled"}</span>
              <span className={"h-5 w-9 rounded-full p-0.5 "+(whatsapp?"bg-onko-teal":"bg-onko-line")}><span className={"block h-4 w-4 rounded-full bg-white transition "+(whatsapp?"translate-x-4":"")}/></span>
            </button>
          </div>
        </div>
        <LanguagePreview language={language}/>
        <button onClick={()=>{window.localStorage.setItem("onko-language",language);window.dispatchEvent(new Event("onko-language-change"));setSaved(true)}} className="onko-button-primary mt-4">Save prototype preferences</button>
        {saved&&<p className="mt-3 text-[13px] font-semibold text-onko-teal">Preferences updated in this UI session.</p>}
      </section>
    </div>
  );
}
