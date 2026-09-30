import type { AttentionLabel, EventStatus } from "./types";

export const labelText: Record<AttentionLabel, string> = {
  SOS: "SOS", NEEDS_REVIEW: "Needs review", QUERY: "Query", FOLLOW_UP: "Follow-up",
};

export const statusText: Record<EventStatus, string> = {
  UPCOMING: "Upcoming", CURRENT: "Today", COMPLETED: "Completed", REPORTED_MISSED: "Reported missed",
  NO_RESPONSE: "No response", RESCHEDULED: "Rescheduled", CONFLICTING: "Conflicting response",
};

export const fmtDate = (iso: string) =>
  new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
export const fmtTime = (iso: string) =>
  new Date(iso).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
