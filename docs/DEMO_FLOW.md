# The one flow that must work

1. **Doctor** opens Care Plan Copilot for Rajesh Kumar, types:
   "Cycle 5 chemo on 15 Oct. Capecitabine 500mg BD after food for 14 days. Ondansetron before chemo. CBC on 13 Oct. Review on 16 Oct."
2. Copilot returns structured items → doctor edits one date → **Approve**.
3. Patient timeline fills with the new events.
4. Patient gets today's **WhatsApp checklist** → marks evening Capecitabine as missed.
5. Patient sends "Hi" → Query → "feeling nauseous since yesterday" → classified SYMPTOM_CONCERN, summarized, routed to care team.
6. Doctor dashboard: **Explainable Attention Queue** shows Rajesh with factual reasons.
7. Doctor opens **Patient 360** → "Since your last review" summary + CBC shown as `Hb: 9.2 — CBC, 20 Sep` (no interpretation).
8. Patient taps **SOS** → caregiver + care team notified, SOS item at top of queue.
9. (Bonus) Doctor sets journey state to Palliative → reminders change tone; Deceased → messaging hard-stops.

Everything else in the spec is a bonus. If time runs out, cut from the bottom.
