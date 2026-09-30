"use client";
import {Printer} from "lucide-react";
export default function PrintSummaryButton(){return <button onClick={()=>window.print()} className="onko-button-primary"><Printer size={17}/>Print care summary</button>}
