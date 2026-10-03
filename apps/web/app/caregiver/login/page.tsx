"use client";
import Link from "next/link";
import {useState,type FormEvent} from "react";
import {useRouter} from "next/navigation";
import {ArrowRight,HeartHandshake,KeyRound,ShieldCheck} from "lucide-react";
import {api} from "@/lib/api";

export default function CaregiverLoginPage(){
 const router=useRouter();
 const [caregiverId,setCaregiverId]=useState(""),[password,setPassword]=useState(""),[busy,setBusy]=useState(false),[error,setError]=useState("");

 async function submit(e:FormEvent){
   e.preventDefault();
   if(!caregiverId.trim()||!password.trim())return;
   setBusy(true);setError("");
   try{
     const result=await api.caregiverLogin(caregiverId.trim(),password.trim());
     document.cookie=`onko_caregiver_id=${encodeURIComponent(result.caregiver_id)}; path=/; SameSite=Lax`;
     window.sessionStorage.setItem("onko-caregiver-id",result.caregiver_id);
     router.push("/caregiver");
     router.refresh();
   }catch(err){setError(err instanceof Error?err.message:"Unable to sign in")}
   finally{setBusy(false)}
 }

 return <main className="min-h-screen bg-onko-canvas">
  <header className="border-b border-onko-line bg-white/90 backdrop-blur-xl"><div className="mx-auto flex h-20 max-w-[1180px] items-center justify-between px-5 md:px-10"><Link href="/" className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-2xl bg-onko-teal text-base font-bold text-white">O</span><div><div className="text-xl font-bold tracking-tight text-onko-teal">OnKo</div><div className="text-[11px] font-medium text-onko-muted">Cancer Care Companion</div></div></Link><span className="hidden items-center gap-2 rounded-full bg-onko-softteal px-3 py-2 text-[12px] font-semibold text-onko-teal sm:flex"><ShieldCheck size={15}/>Caregiver access</span></div></header>
  <section className="mx-auto grid min-h-[calc(100vh-80px)] max-w-[1180px] items-center gap-10 px-5 py-12 md:grid-cols-[1fr_.85fr] md:px-10">
   <div><span className="grid h-14 w-14 place-items-center rounded-2xl bg-onko-softteal text-onko-teal"><HeartHandshake size={26}/></span><p className="onko-eyebrow mt-6">Consent-based support</p><h1 className="mt-2 max-w-xl text-[42px] font-bold leading-[1.08] tracking-tight sm:text-[54px]">Support their care journey, with the access they choose to share.</h1><p className="mt-5 max-w-xl text-[16px] leading-7 text-onko-muted">Use the caregiver ID and reusable password sent to your WhatsApp number when the patient grants access.</p></div>
   <form onSubmit={submit} className="onko-card p-6 sm:p-8"><span className="grid h-12 w-12 place-items-center rounded-xl bg-onko-softteal text-onko-teal"><KeyRound size={21}/></span><h2 className="mt-5 text-[27px] font-bold">Caregiver sign in</h2><p className="mt-2 text-[13px] leading-6 text-onko-muted">One login works for every caregiver account. Access remains controlled by the linked patient.</p>
    <label className="mt-6 block text-[13px] font-semibold">Caregiver ID<input autoComplete="username" value={caregiverId} onChange={e=>setCaregiverId(e.target.value)} placeholder="Enter caregiver ID" className="mt-2 w-full rounded-xl border border-onko-line bg-white p-3.5 font-normal outline-none focus:border-onko-teal"/></label>
    <label className="mt-4 block text-[13px] font-semibold">Password<input autoComplete="current-password" type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Enter password" className="mt-2 w-full rounded-xl border border-onko-line bg-white p-3.5 font-normal outline-none focus:border-onko-teal"/></label>
    {error&&<div className="mt-4 rounded-xl border border-red-100 bg-red-50 p-3 text-[12px] text-onko-sos">{error}</div>}
    <button disabled={busy||!caregiverId.trim()||!password.trim()} className="onko-button-primary mt-5 w-full justify-center disabled:opacity-50">{busy?"Signing in…":"Open caregiver dashboard"}<ArrowRight size={16}/></button>
    <p className="mt-5 text-center text-[11px] leading-5 text-onko-muted">No credentials yet? The patient can add you from their Profile & access page.</p>
   </form>
  </section>
 </main>
}
