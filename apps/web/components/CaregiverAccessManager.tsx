"use client";

import {useState} from "react";
import {UserPlus,MessageCircle} from "lucide-react";
import type {Caregiver,Patient} from "@/lib/types";
import {api,type CaregiverInviteResult} from "@/lib/api";
import CaregiverLifecycle from "@/components/CaregiverLifecycle";

export default function CaregiverAccessManager({patient,initial}:{patient:Patient;initial:Caregiver[]}){
  const [caregivers,setCaregivers]=useState(initial);
  const [form,setForm]=useState({name:"",relation:"",phone:"",type:"family"});
  const [busy,setBusy]=useState(false),[error,setError]=useState(""),[result,setResult]=useState<CaregiverInviteResult|null>(null);

  async function add(){
    if(!form.name.trim()||!form.relation.trim()||!form.phone.trim())return;
    setBusy(true);setError("");setResult(null);
    try{
      const r=await api.addCaregiver(patient.id,{
        name:form.name.trim(),
        relation:form.relation.trim(),
        phone_whatsapp:form.phone.trim(),
        type:form.type,
      });
      setResult(r);
      setCaregivers(list=>[...list.filter(c=>c.id!==r.caregiver.id),r.caregiver]);
      setForm({name:"",relation:"",phone:"",type:"family"});
    }catch(e){setError(e instanceof Error?e.message:"Unable to add caregiver")}
    finally{setBusy(false)}
  }

  return <div className="mt-5 space-y-5">
    <section className="onko-card p-5">
      <div className="flex items-center gap-3"><UserPlus size={19} className="text-onko-teal"/><div><h3 className="text-[18px] font-bold">Add caregiver</h3><p className="mt-1 text-[12px] text-onko-muted">You control who can access your caregiver dashboard view.</p></div></div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Field label="Caregiver name" value={form.name} onChange={v=>setForm(x=>({...x,name:v}))}/>
        <Field label="Relation" value={form.relation} onChange={v=>setForm(x=>({...x,relation:v}))} placeholder="e.g. Daughter, Husband"/>
        <Field label="WhatsApp number" value={form.phone} onChange={v=>setForm(x=>({...x,phone:v}))} placeholder="+91..."/>
        <label className="text-[13px] font-semibold">Type<select value={form.type} onChange={e=>setForm(x=>({...x,type:e.target.value}))} className="mt-2 w-full rounded-xl border border-onko-line bg-white p-3 font-normal"><option value="family">Family</option><option value="professional">Professional</option></select></label>
      </div>
      <div className="mt-4 flex gap-3 rounded-xl bg-onko-softteal/60 p-4 text-[13px] leading-5 text-onko-muted"><MessageCircle size={18} className="shrink-0 text-onko-teal"/>The caregiver receives a common OnKo caregiver login link, caregiver ID and reusable password on WhatsApp.</div>
      <button disabled={busy||!form.name.trim()||!form.relation.trim()||!form.phone.trim()} onClick={()=>void add()} className="onko-button-primary mt-4 disabled:opacity-50"><UserPlus size={16}/>{busy?"Adding caregiver…":"Grant caregiver access"}</button>
      {result&&<div className="mt-4 rounded-xl bg-onko-softteal p-4 text-[13px]"><strong className="text-onko-teal">Caregiver access created</strong><p className="mt-1">Caregiver ID: <b>{result.login_id}</b></p><p className="mt-1 text-onko-muted">{result.whatsapp_sent?"Login credentials were sent by WhatsApp.":result.warning||"WhatsApp delivery was not confirmed."}</p>{result.demo_password&&<p className="mt-2 font-semibold text-onko-teal">Demo password: {result.demo_password}</p>}</div>}
      {error&&<p className="mt-4 rounded-xl bg-red-50 p-3 text-[12px] text-onko-sos">{error}</p>}
    </section>

    {caregivers.length?caregivers.map(c=><CaregiverLifecycle key={c.id} caregiver={c} mode="patient"/>):<section className="onko-card p-5 text-[14px] text-onko-muted">No caregiver is currently linked to this patient.</section>}
  </div>
}

function Field({label,value,onChange,placeholder=""}:{label:string;value:string;onChange:(v:string)=>void;placeholder?:string}){
  return <label className="text-[13px] font-semibold">{label}<input value={value} onChange={e=>onChange(e.target.value)} placeholder={placeholder} className="mt-2 w-full rounded-xl border border-onko-line bg-white p-3 font-normal outline-none focus:border-onko-teal"/></label>
}
