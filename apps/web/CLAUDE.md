# Folder: apps/web — owner: Niya

You may ONLY edit files inside `apps/web/`.
Do not edit `contracts/`, `apps/api/` or root files.

- Types in `lib/types.ts` mirror `contracts/schemas.json`. Don't rename fields.
- ALL data goes through `lib/api.ts`. Never call fetch() directly in components.
- `NEXT_PUBLIC_USE_MOCKS=true` → reads `mocks/*.json`. Keep mocks matching the contract.
- UI language rules (product safety):
  - Attention labels: "Needs review", "Follow-up", "Query", "SOS". Never "High risk", never a risk score.
  - Show lab values as-is: "Hb: 9.2 g/dL — CBC, 20 Sep". No red/green colouring of values, no arrows.
  - Care Plan Copilot shows AI items as an editable DRAFT with a clear "Approve plan" button.
  - Always visible footer note on doctor screens: "OnKo organizes recorded activity. Clinical interpretation stays with the care team."
- Theme: deep teal primary (#0F5F5C), soft mint surfaces — match the mockups in the spec PDF.
