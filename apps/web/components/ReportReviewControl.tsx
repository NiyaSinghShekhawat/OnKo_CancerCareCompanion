"use client";
import {useState} from "react";
import {CheckCircle2} from "lucide-react";
export default function ReportReviewControl({reviewed}:{reviewed:boolean}){const [done,setDone]=useState(reviewed);return <button onClick={()=>setDone(true)} disabled={done} className={"onko-button-secondary disabled:opacity-70 "+(done?"text-onko-teal":"")}>{done?<><CheckCircle2 size={15}/>Reviewed</>:<>Mark reviewed</>}</button>}