"use client";
import {useState} from "react";
import {useRouter} from "next/navigation";
import {Check,ChevronLeft,ChevronRight,KeyRound,MessageCircle,Phone,ShieldCheck,UserPlus,X} from "lucide-react";
import {api,type EnrollmentResult} from "@/lib/api";

const steps=["Patient","Contact","Verify","Care","Access"];

export default function EnrollPatientPrototype(){
 const router=useRouter();
 const [open,setOpen]=useState(false),[step,setStep]=useState(0),[verified,setVerified]=useState(false);
 const [otpSent,setOtpSent]=useState(false),[otp,setOtp]=useState(""),[busy,setBusy]=useState(false),[error,setError]=useState("");
 const [result,setResult]=useState<EnrollmentResult|null>(null);
 const [form,setForm]=useState({name:"",age:"",gender:"",language:"English",phone:"",diagnosis:"",regimen:"",cycleCurrent:"",cycleTotal:"",abha:""});
 const set=(k:string,v:string)=>setForm(x=>({...x,[k]:v}));

 function reset(){
   setStep(0);setVerified(false);setOtpSent(false);setOtp("");setError("");setResult(null);
   setForm({name:"",age:"",gender:"",language:"English",phone:"",diagnosis:"",regimen:"",cycleCurrent:"",cycleTotal:"",abha:""});
 }

 async function sendOtp(){
   if(!form.phone.trim())return;
   setBusy(true);setError("");
   try{
     const r=await api.sendEnrollmentOtp(form.phone.trim());
     setOtpSent(true);
     if(r.demo_otp)setOtp(r.demo_otp);
     if(!r.sent&&!r.demo_otp)setError("OTP was created, but WhatsApp delivery is not configured. Configure Twilio or enable ONKO_DEMO_OTP_ECHO for local testing.");
   }catch(e){setError(e instanceof Error?e.message:"Unable to send verification code")}
   finally{setBusy(false)}
 }

 async function verifyOtp(){
   if(!otp.trim())return;
   setBusy(true);setError("");
   try{
     await api.verifyEnrollmentOtp(form.phone.trim(),otp.trim());
     setVerified(true);
   }catch(e){setError(e instanceof Error?e.message:"Unable to verify code")}
   finally{setBusy(false)}
 }

 async function complete(){
   setBusy(true);setError("");
   try{
     const r=await api.enrollPatient({
       name:form.name.trim(),
       age:Number(form.age),
       gender:form.gender,
       preferred_language:form.language,
       phone:form.phone.trim(),
       abha_id:form.abha.trim()||null,
       diagnosis_label:form.diagnosis.trim(),
       regimen_label:form.regimen.trim(),
       cycle_current:Number(form.cycleCurrent||0),
       cycle_total:Number(form.cycleTotal||0),
     });
     setResult(r);
     router.refresh();
   }catch(e){setError(e instanceof Error?e.message:"Unable to enroll patient")}
   finally{setBusy(false)}
 }

 const canContinue=
   step===0?Boolean(form.name.trim()&&form.age&&form.gender):
   step===1?Boolean(form.phone.trim()):
   step===2?verified:
   step===3?Boolean(form.diagnosis.trim()):
   true;

 return <><button onClick={()=>{reset();setOpen(true)}} className="onko-button-primary"><UserPlus size={15}/>Enroll new patient</button>
 {open&&<div className="fixed inset-0 z-50 overflow-y-auto bg-black/35 p-3 sm:p-6"><div className="mx-auto my-4 w-full max-w-3xl rounded-3xl bg-white shadow-2xl" role="dialog" aria-modal="true" aria-labelledby="enroll-title">
  <div className="flex items-start justify-between border-b border-onko-line p-5 sm:p-7"><div><p className="onko-eyebrow">Doctor-led patient onboarding</p><h2 id="enroll-title" className="mt-1 text-[24px] font-bold">Enroll patient</h2><p className="mt-1 text-[13px] text-onko-muted">Create the patient record, verify WhatsApp and deliver dashboard access.</p></div><button onClick={()=>setOpen(false)} aria-label="Close enrollment"><X/></button></div>
  <div className="overflow-x-auto border-b border-onko-line px-5 py-4 sm:px-7"><div className="flex min-w-[560px] items-center">{steps.map((s,i)=><div key={s} className="flex flex-1 items-center"><span className={"grid h-8 w-8 shrink-0 place-items-center rounded-full text-[12px] font-bold "+(i<step?"bg-onko-teal text-white":i===step?"border-2 border-onko-teal bg-onko-softteal text-onko-teal":"bg-onko-surface text-onko-muted")}>{i<step?<Check size={14}/>:i+1}</span><span className={"ml-2 text-[12px] font-semibold "+(i<=step?"text-onko-ink":"text-onko-muted")}>{s}</span>{i<steps.length-1&&<span className="mx-3 h-px flex-1 bg-onko-line"/>}</div>)}</div></div>
  <div className="p-5 sm:p-7">
   {step===0&&<div><StepTitle title="Patient details" text="Basic identifying information recorded by the care team."/><div className="mt-5 grid gap-3 sm:grid-cols-2"><Field label="Full name" value={form.name} onChange={v=>set("name",v)}/><Field label="Age" value={form.age} onChange={v=>set("age",v)} type="number"/><label className="text-[13px] font-semibold">Gender<select value={form.gender} onChange={e=>set("gender",e.target.value)} className="mt-2 w-full rounded-xl border border-onko-line bg-white p-3"><option value="">Select</option><option>Male</option><option>Female</option><option>Other</option></select></label><label className="text-[13px] font-semibold">Preferred language<select value={form.language} onChange={e=>set("language",e.target.value)} className="mt-2 w-full rounded-xl border border-onko-line bg-white p-3"><option>English</option><option>Hindi</option><option>Telugu</option></select></label><Field label="ABHA ID (optional)" value={form.abha} onChange={v=>set("abha",v)} placeholder="Can be linked later"/></div></div>}
   {step===1&&<div><StepTitle title="Patient contact" text="This number becomes the patient's verified WhatsApp and login-delivery contact."/><div className="mt-5"><Field label="WhatsApp / mobile number" value={form.phone} onChange={v=>{set("phone",v);setVerified(false);setOtpSent(false);setOtp("")}} placeholder="+91 …"/></div><div className="mt-4 flex gap-3 rounded-xl bg-onko-softteal p-4"><MessageCircle className="shrink-0 text-onko-teal"/><p className="text-[13px] leading-5 text-onko-muted">OnKo sends an OTP to verify this number. After enrollment, the same number receives the patient ID, password and dashboard login link.</p></div></div>}
   {step===2&&<div><StepTitle title="Verify WhatsApp number" text={"Confirm that "+(form.phone||"the entered number")+" is reachable before creating patient access."}/>{!verified?<div className="mt-5 rounded-2xl bg-onko-surface p-5"><div className="flex gap-3"><Phone className="text-onko-teal"/><div><strong>WhatsApp verification</strong><p className="mt-1 text-[12px] leading-5 text-onko-muted">The code expires in 10 minutes and is validated by the backend.</p></div></div><button disabled={busy} onClick={sendOtp} className="onko-button-secondary mt-4 disabled:opacity-50">{otpSent?"Resend code":"Send verification code"}</button>{otpSent&&<div className="mt-4 flex flex-col gap-3 sm:flex-row"><input value={otp} onChange={e=>setOtp(e.target.value)} aria-label="OTP" inputMode="numeric" maxLength={6} placeholder="Enter 6-digit OTP" className="min-w-0 flex-1 rounded-xl border border-onko-line bg-white p-3 tracking-[.35em]"/><button disabled={busy||otp.length<6} onClick={verifyOtp} className="onko-button-primary disabled:opacity-50">Verify OTP</button></div>}</div>:<div className="mt-5 flex gap-3 rounded-2xl bg-onko-softteal p-5"><ShieldCheck className="text-onko-teal"/><div><strong className="text-onko-teal">WhatsApp number verified</strong><p className="mt-1 text-[12px] text-onko-muted">Enrollment can now create the patient record and dashboard access.</p></div></div>}</div>}
   {step===3&&<div><StepTitle title="Clinician-recorded care information" text="These fields are entered by the clinician. OnKo does not generate a diagnosis or treatment plan."/><div className="mt-5 grid gap-3 sm:grid-cols-2"><div className="sm:col-span-2"><Field label="Diagnosis label" value={form.diagnosis} onChange={v=>set("diagnosis",v)}/></div><div className="sm:col-span-2"><Field label="Regimen / care-plan label" value={form.regimen} onChange={v=>set("regimen",v)}/></div><Field label="Current cycle" value={form.cycleCurrent} onChange={v=>set("cycleCurrent",v)} type="number"/><Field label="Total cycles" value={form.cycleTotal} onChange={v=>set("cycleTotal",v)} type="number"/></div><p className="mt-4 text-[11px] leading-5 text-onko-muted">Detailed medicines, investigations, procedures, appointments and milestones remain part of the clinician-approved Care Plan workflow after enrollment.</p></div>}
   {step===4&&<div><StepTitle title="Review & create patient access" text="This writes the patient to the configured database and sends dashboard credentials over WhatsApp."/><div className="mt-5 grid gap-3 sm:grid-cols-2"><Review label="Patient" value={form.name||"Not entered"}/><Review label="Verified number" value={form.phone||"Not entered"}/><Review label="Language" value={form.language}/><Review label="Care context" value={[form.regimen,(form.cycleCurrent&&form.cycleTotal)?("Cycle "+form.cycleCurrent+" of "+form.cycleTotal):""].filter(Boolean).join(" · ")||"Not entered"}/></div><div className="mt-5 rounded-2xl border border-onko-line p-5"><div className="flex gap-3"><KeyRound className="text-onko-teal"/><div><strong>Patient dashboard access</strong><p className="mt-1 text-[13px] leading-6 text-onko-muted">OnKo creates a patient ID plus a reusable password. Only the password hash is stored in the database; the password is delivered through WhatsApp and remains valid until changed.</p></div></div></div>{result&&<div className="mt-4 rounded-2xl bg-onko-softteal p-5"><strong className="text-onko-teal">Patient enrolled successfully</strong><p className="mt-1 text-[13px]">Patient ID: <b>{result.login_id}</b></p><p className="mt-1 text-[12px] leading-5 text-onko-muted">{result.whatsapp_sent?"WhatsApp login credentials were sent to the verified number.":result.warning||"WhatsApp delivery was not confirmed."}</p>{result.demo_password&&<p className="mt-2 text-[12px] font-semibold text-onko-teal">Demo password: {result.demo_password}</p>}</div>}</div>}
   {error&&<div className="mt-5 rounded-xl border border-red-100 bg-red-50 p-3 text-[12px] text-onko-sos">{error}</div>}
  </div>
  <div className="flex flex-wrap items-center justify-between gap-3 border-t border-onko-line p-5 sm:px-7"><button disabled={step===0||busy||Boolean(result)} onClick={()=>setStep(s=>Math.max(0,s-1))} className="onko-button-secondary disabled:opacity-40"><ChevronLeft size={15}/>Back</button>{step<4?<button disabled={!canContinue||busy} onClick={()=>setStep(s=>Math.min(4,s+1))} className="onko-button-primary disabled:opacity-40">Continue<ChevronRight size={15}/></button>:result?<button onClick={()=>setOpen(false)} className="onko-button-primary">Done</button>:<button disabled={busy} onClick={complete} className="onko-button-primary disabled:opacity-50"><UserPlus size={15}/>{busy?"Creating patient…":"Complete enrollment"}</button>}</div>
 </div></div>}</>}

function StepTitle({title,text}:{title:string;text:string}){return <div><h3 className="text-[20px] font-bold">{title}</h3><p className="mt-1 text-[13px] leading-6 text-onko-muted">{text}</p></div>}
function Field({label,value,onChange,type="text",placeholder=""}:{label:string;value:string;onChange:(v:string)=>void;type?:string;placeholder?:string}){return <label className="text-[13px] font-semibold">{label}<input type={type} value={value} onChange={e=>onChange(e.target.value)} placeholder={placeholder} className="mt-2 w-full rounded-xl border border-onko-line bg-white p-3 font-normal outline-none focus:border-onko-teal"/></label>}
function Review({label,value}:{label:string;value:string}){return <div className="rounded-xl bg-onko-surface p-4"><p className="text-[11px] font-bold uppercase tracking-wide text-onko-muted">{label}</p><p className="mt-1 text-[14px] font-semibold">{value}</p></div>}
