# Sentry Gate — AI Document Screening Dashboard

Frontend-only demo dashboard for a hackathon "AI-Based Fake Identity & Document
Screening System." Built with Next.js 14 (App Router), TypeScript, and
Tailwind CSS. All data is mocked in `lib/mock-data.ts` — there is no backend.

## Requirements
- Node.js 18.18+ (Node 20 LTS recommended)
- npm 9+

## Setup

```bash
# 1. Unzip the project, then move into it
cd border-screening

# 2. Install dependencies
npm install

# 3. Run the dev server
npm run dev
```

Open http://localhost:3000 in your browser.

## Scripts
- `npm run dev` — start the dev server with hot reload
- `npm run build` — production build (also type-checks)
- `npm start` — serve the production build (run `build` first)
- `npm run lint` — run ESLint

## Where things live
- `app/page.tsx` — Dashboard overview (stat cards + recent scans table)
- `app/scan/page.tsx` — Screening Terminal (idle → scanning → results workflow)
- `app/database/page.tsx`, `app/settings/page.tsx` — supporting nav pages
- `components/` — Sidebar, Topbar, DocumentUpload, AIViewer, ExtractedData,
  RiskScorePanel, ScanningState, DecisionBanner, StatCard, ScansTable
- `lib/mock-data.ts` — all mock records, the demo "flagged" document case,
  and its bounding-box coordinates
- `lib/types.ts` — shared TypeScript types
- `lib/utils.ts` — small formatting/style helpers

## Demo flow
1. Go to **New Scan** in the sidebar.
2. Click "Use sample document instead" (or drop any image) to trigger the
   simulated ~2s AI processing delay.
3. Review the three result panels: the Forensic Viewer (hover the glowing
   red/amber boxes for tooltips), the VIZ vs MRZ cross-check (mismatched
   fields glow red), and the Risk Assessment panel.
4. Click **Approve Entry**, **Secondary Inspection**, or **Reject** to see
   the decision banner.

To try a different scenario, edit `mockDocumentCase` in `lib/mock-data.ts` —
adjust `riskScore`, `fields`, or `tamperedRegions` (percentages are relative
to the image container, so `left`/`top`/`width`/`height` all range 0–100).
