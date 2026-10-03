"use client";

import {useEffect,useMemo,useState} from "react";
import {KeyRound,MessageCircle,UserPlus} from "lucide-react";
import type {Caregiver,Patient} from "@/lib/types";
import {api,type CaregiverInviteResult} from "@/lib/api";
import CaregiverLifecycle from "@/components/CaregiverLifecycle";

const PASS_KEY="onko-caregiver-passwords";

function loadPasswords():Record<string,string>{
  if(typeof window==="undefined") return {};
  try{return JSON.parse(window.sessionStorage.getItem(PASS_KEY)||"{}")}catch{return {}}
}
function savePasswords(value:Record<string,string>){
  if(typeof window!=="undefined") window.sessionStorage.setItem(PASS_KEY,JSON.stringify(value));
}

export default function CaregiverAccessManager({patient,initial}:{patient:Patient;initial:Caregiver[]}){
  const [caregivers,setCaregivers]=useState(initial);
  const [passwords,setPasswords]=useState<Record<string,string>>({});
  const [form,setForm]=useState({name:"",relation:"",phone:"",type:"family"});
  const [busy,setBusy]=useState(false),[error,setError]=useState(""),[result,setResult]=useState<CaregiverInviteResult|null>(null);

  useEffect(()=>setPasswords(loadPasswords()),[]);
  const caregiverMap=useMemo(()=>new Map(caregivers.map(c=>[c.id,c])),[caregivers]);

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
      const plain=r.password||r.demo_password;
      if(plain){
        const next={...loadPasswords(),[r.caregiver.id]:plain};
        savePasswords(next);
        setPasswords(next);
      }
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
      {result&&<div className="mt-4 rounded-xl bg-onko-softteal p-4 text-[13px]"><strong className="text-onko-teal">Caregiver access created</strong><p className="mt-1">Caregiver ID: <b>{result.login_id}</b></p><p className="mt-1 text-onko-muted">{result.whatsapp_sent?"Login credentials were sent by WhatsApp.":result.warning||"WhatsApp delivery was not confirmed."}</p>{(result.password||result.demo_password)&&<p className="mt-2 font-semibold text-onko-teal">Password: {result.password||result.demo_password}</p>}</div>}
      {error&&<p className="mt-4 rounded-xl bg-red-50 p-3 text-[12px] text-onko-sos">{error}</p>}
    </section>

    {caregivers.length?caregivers.map(c=><section key={c.id} className="space-y-3">
      <div className="onko-card p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div><p className="onko-eyebrow">Caregiver details</p><h3 className="mt-1 text-[20px] font-bold">{c.name}</h3><p className="mt-1 text-[13px] text-onko-muted">{c.relation} · {c.type}</p></div>
          <span className="rounded-full bg-onko-softteal px-3 py-1.5 text-[12px] font-bold text-onko-teal">{c.consent_status}</span>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <Detail label="WhatsApp" value={c.phone_whatsapp}/>
          <Detail label="Caregiver ID" value={c.id}/>
          <Detail label="Password" value={passwords[c.id]||"Not stored — sent on WhatsApp"}/>
          <Detail label="Linked patient" value={patient.name}/>
        </div>
        <div className="mt-4 flex gap-3 rounded-xl bg-onko-surface p-4 text-[12px] leading-5 text-onko-muted"><KeyRound size={17} className="shrink-0 text-onko-teal"/>For security, OnKo stores only the password hash in the database. The plain password is shown here only during this browser session after caregiver access is created.</div>
      </div>
      <CaregiverLifecycle caregiver={caregiverMap.get(c.id)||c} mode="patient"/>
    </section>):<section className="onko-card p-5 text-[14px] text-onko-muted">No caregiver is currently linked to this patient.</section>}
  </div>
}

function Field({label,value,onChange,placeholder=""}:{label:string;value:string;onChange:(v:string)=>void;placeholder?:string}){
  return <label className="text-[13px] font-semibold">{label}<input value={value} onChange={e=>onChange(e.target.value)} placeholder={placeholder} className="mt-2 w-full rounded-xl border border-onko-line bg-white p-3 font-normal outline-none focus:border-onko-teal"/></label>
}
function Detail({label,value}:{label:string;value:string}){
  return <div className="rounded-xl bg-onko-surface p-4"><p className="text-[11px] font-bold uppercase text-onko-muted">{label}</p><p className="mt-1 break-all text-[14px] font-semibold">{value}</p></div>
}
