"use client";
import Link from "next/link";
import {useState,type FormEvent} from "react";
import {useRouter} from "next/navigation";
import {ArrowRight,HeartHandshake,KeyRound,ShieldCheck} from "lucide-react";
import {api} from "@/lib/api";

export default function PatientLoginPage(){
 const router=useRouter();
 const [patientId,setPatientId]=useState(""),[password,setPassword]=useState(""),[busy,setBusy]=useState(false),[error,setError]=useState("");

 async function submit(e:FormEvent){
   e.preventDefault();
   if(!patientId.trim()||!password.trim())return;
   setBusy(true);setError("");
   try{
     const result=await api.patientLogin(patientId.trim(),password.trim());
     document.cookie=`onko_patient_id=${encodeURIComponent(result.patient_id)}; path=/; SameSite=Lax`;
     window.sessionStorage.setItem("onko-patient-id",result.patient_id);
     window.sessionStorage.setItem("onko-patient-password",password.trim());
     router.push("/patient");
     router.refresh();
   }catch(err){setError(err instanceof Error?err.message:"Unable to sign in")}
   finally{setBusy(false)}
 }

 return <main className="min-h-screen bg-onko-canvas">
  <header className="border-b border-onko-line bg-white/90 backdrop-blur-xl"><div className="mx-auto flex h-20 max-w-[1180px] items-center justify-between px-5 md:px-10"><Link href="/" className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-2xl bg-onko-teal text-base font-bold text-white">O</span><div><div className="text-xl font-bold tracking-tight text-onko-teal">OnKo</div><div className="text-[11px] font-medium text-onko-muted">Cancer Care Companion</div></div></Link><span className="hidden items-center gap-2 rounded-full bg-onko-softteal px-3 py-2 text-[12px] font-semibold text-onko-teal sm:flex"><ShieldCheck size={15}/>Patient access</span></div></header>
  <section className="mx-auto grid min-h-[calc(100vh-80px)] max-w-[1180px] items-center gap-10 px-5 py-12 md:grid-cols-[1fr_.85fr] md:px-10">
   <div><span className="grid h-14 w-14 place-items-center rounded-2xl bg-onko-softteal text-onko-teal"><HeartHandshake size={26}/></span><p className="onko-eyebrow mt-6">Your care journey, connected</p><h1 className="mt-2 max-w-xl text-[42px] font-bold leading-[1.08] tracking-tight sm:text-[54px]">Welcome back to your OnKo dashboard.</h1><p className="mt-5 max-w-xl text-[16px] leading-7 text-onko-muted">Use the patient ID and password sent to your verified WhatsApp number by your care team.</p><div className="mt-6 rounded-2xl border border-onko-line bg-white p-5 text-[13px] leading-6 text-onko-muted"><strong className="text-onko-ink">Care stays clinician-led.</strong> OnKo organizes recorded care information and communication; it does not diagnose or recommend treatment.</div></div>
   <form onSubmit={submit} className="onko-card p-6 sm:p-8"><span className="grid h-12 w-12 place-items-center rounded-xl bg-onko-softteal text-onko-teal"><KeyRound size={21}/></span><h2 className="mt-5 text-[27px] font-bold">Patient sign in</h2><p className="mt-2 text-[13px] leading-6 text-onko-muted">Your credentials are issued only after your care team verifies the registered WhatsApp number.</p>
    <label className="mt-6 block text-[13px] font-semibold">Patient ID<input autoComplete="username" value={patientId} onChange={e=>setPatientId(e.target.value)} placeholder="e.g. p_rajesh or your issued ID" className="mt-2 w-full rounded-xl border border-onko-line bg-white p-3.5 font-normal outline-none focus:border-onko-teal"/></label>
    <label className="mt-4 block text-[13px] font-semibold">Password<input autoComplete="current-password" type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Enter password" className="mt-2 w-full rounded-xl border border-onko-line bg-white p-3.5 font-normal outline-none focus:border-onko-teal"/></label>
    {error&&<div className="mt-4 rounded-xl border border-red-100 bg-red-50 p-3 text-[12px] text-onko-sos">{error}</div>}
    <button disabled={busy||!patientId.trim()||!password.trim()} className="onko-button-primary mt-5 w-full justify-center disabled:opacity-50">{busy?"Signing in…":"Open patient dashboard"}<ArrowRight size={16}/></button>
    <p className="mt-5 text-center text-[11px] leading-5 text-onko-muted">No credentials yet? Ask your care team to enroll you and verify your WhatsApp number.</p>
   </form>
  </section>
 </main>
}
