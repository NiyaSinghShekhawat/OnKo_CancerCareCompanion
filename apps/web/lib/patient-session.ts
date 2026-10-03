import {cookies} from "next/headers";

export const PATIENT_ID_COOKIE="onko_patient_id";

export function currentPatientId(searchParams?:{id?:string}){
  const fromQuery=searchParams?.id?.trim();
  if(fromQuery)return fromQuery;
  const fromCookie=cookies().get(PATIENT_ID_COOKIE)?.value?.trim();
  return fromCookie||"p_rajesh";
}
