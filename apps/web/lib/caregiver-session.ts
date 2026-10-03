import {cookies} from "next/headers";
import {redirect} from "next/navigation";

export const CAREGIVER_ID_COOKIE="onko_caregiver_id";

export function currentCaregiverId(){
  const id=cookies().get(CAREGIVER_ID_COOKIE)?.value?.trim();
  if(!id) redirect("/caregiver/login");
  return id;
}
