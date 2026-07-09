# Bridge Crack Detection System — Enhancement Plan
**SensorX Challenge 2026**
**Date:** July 9, 2026

## Goal

Move the project from "crack detector + sensor dashboard" to a **predictive infrastructure-risk platform**, by adding three features that build on data already in the schema:

1. Crack Growth Trend
2. Predictive Maintenance Window
3. Multi-Bridge Risk Map (GIS)

These are sequenced deliberately: #2 depends on #1's data. #3 is independent and can be built in parallel by a second team member.

---

## Why these three

| Feature | Uses existing schema? | New concept for judges | Effort |
|---|---|---|---|
| Growth trend | Yes (`previous_crack_id`, unused) | "We track cracks over time, not just single snapshots" | Low |
| Predictive window | Yes (built on #1) | "We predict *when* action is needed, not just severity" | Low |
| Risk map | Partial (`city` exists, needs lat/lng) | "This is a fleet-level city infrastructure tool" | Low–Medium |

---

## Feature 1: Crack Growth Trend

**Objective:** Link the same physical crack across multiple inspections and visualize how it has grown.

### Backend Tasks
- [ ] Create `backend/crack_linking.py` with `link_to_previous_crack()`
  - Matches new detections to prior detections on the same bridge via bounding-box center distance
  - On match, sets `previous_crack_id` and copies `crack_identifier` (lineage ID)
- [ ] Call `link_to_previous_crack()` inside `/detect/{bridge_id}/save` right after a new detection is saved
- [ ] Add `GET /crack/{crack_id}/history` endpoint
  - Walks the `previous_crack_id` chain backward to build a chronological timeline
  - Returns: list of `{detected_at, area, width, height, confidence, severity_level}`
  - Computes `growth_pct` and `growth_per_day` from first → last data point

### Frontend Tasks
- [ ] Create `components/CrackGrowthChart.jsx`
  - Fetches `/crack/{crackId}/history`
  - Reuses existing `SimpleLineChart` pattern from `SensorMonitor.jsx` (x = detected_at, y = area)
  - Shows "Not enough inspection history yet" if < 2 data points
  - Bilingual labels (EN/AR) consistent with rest of app
- [ ] Add growth chart to crack detail view in `CrackDetection.jsx` (when engineer clicks a confirmed crack)

### Demo Data (required — real growth isn't observable live)
- [ ] Add seed block to `init_db.py`:
  - One crack lineage (`crack_identifier = "CRK-CAIRO12-001"`) with 3 backdated detections (21 days ago, 10 days ago, today)
  - Increasing area/width/height/severity across the three points
  - Linked via `previous_crack_id`

### Definition of Done
Opening a crack's detail view shows a line chart of area over time and a "+X% since first detection" summary, using seeded data.

---

## Feature 2: Predictive Maintenance Window

**Objective:** Extrapolate the growth rate from Feature 1 into an estimated date the crack becomes critical.

### Backend Tasks
- [ ] Define `CRITICAL_AREA_THRESHOLD` constant (set from your `severity_level = 3` boundary in the data)
- [ ] Add `GET /crack/{crack_id}/prediction` endpoint
  - Reuses `/crack/{crack_id}/history` internally for `growth_per_day` and current area
  - Linear extrapolation: `days_to_critical = (threshold - current_area) / growth_per_day`
  - Handles edge cases: flat/negative growth → "no trend detected"; already over threshold → "immediate inspection required"
  - Returns bilingual message strings (`message_en`, `message_ar`) + `recommended_inspection_date`

### Frontend Tasks
- [ ] Add a "Prediction" callout card under the growth chart in the crack detail view
  - Shows the bilingual message and recommended inspection date
  - Style as an alert (reuse `--warning-color` / `--danger-color` CSS variables)

### Framing for Judges
- [ ] Prepare one slide/talking point stating explicitly: *"This is a linear trend extrapolation from historical detections, not a trained ML forecasting model."* Accurate framing reads as more credible than an overstated AI claim.

### Definition of Done
The seeded crack from Feature 1 shows a prediction card: "~N days to critical width — inspect by [date]."

---

## Feature 3: Multi-Bridge Risk Map (GIS)

**Objective:** Fleet-level view of all bridges, pinned on a map, colored by severity.

### Database Tasks
- [ ] Migration: add `latitude DECIMAL(10,7)` and `longitude DECIMAL(10,7)` to `bridges` table
- [ ] Seed at least 3 real Cairo-area bridges with coordinates:
  - Qasr El-Nile Bridge — 30.0459, 31.2243
  - 6th October Bridge — 30.0571, 31.2272
  - Imbaba Bridge — 30.0771, 31.2089

### Backend Tasks
- [ ] Add `GET /bridges/map` endpoint
  - For each bridge: max severity across its cracks, total crack count, high-severity crack count, lat/lng
  - Single call powers the whole map (no N+1 requests from frontend)

### Frontend Tasks
- [ ] `npm install leaflet react-leaflet`
- [ ] Create `components/BridgeMap.jsx`
  - `MapContainer` centered on Cairo, OpenStreetMap tile layer (no API key needed)
  - `CircleMarker` per bridge, colored by severity (green/orange/red using existing CSS variable colors)
  - Popup on click: bridge name, crack count, high-severity count (bilingual)
- [ ] Add "Fleet Map" / "خريطة الجسور" tab to `Navigation.jsx`

### Definition of Done
New tab shows a live map with 3+ bridges pinned, colored by current severity, clickable for summary info.

---

## Build Order

```
Day 1 (AM):  Feature 1 backend — linking logic + /crack/{id}/history endpoint
Day 1 (PM):  Feature 1 frontend — growth chart component + seed data
Day 2 (AM):  Feature 2 — prediction endpoint + card (fast, builds on Day 1)
Day 2 (PM):  Feature 3 backend — migration + /bridges/map endpoint
             (parallelizable with Day 1–2 if a second person is available)
Day 3 (AM):  Feature 3 frontend — map component + nav tab
Day 3 (PM):  End-to-end test with seeded data, fix edge cases, rehearse demo
```

If working solo and short on time, prioritize in this order: **Feature 1 → Feature 2 → Feature 3** — the first two are cheap and directly strengthen the core detection story; the map is the most visually impressive but least technically differentiating.

---

## File Checklist

**New files**
- `backend/crack_linking.py`
- `components/CrackGrowthChart.jsx`
- `components/BridgeMap.jsx`

**Modified files**
- `backend/main.py` — add `/crack/{id}/history`, `/crack/{id}/prediction`, `/bridges/map`; call `link_to_previous_crack()` in save flow
- `backend/models.py` — add `latitude`, `longitude` to `Bridge` model
- `backend/init_db.py` — add seed data for crack lineage + bridge coordinates
- `components/CrackDetection.jsx` — render growth chart + prediction card in crack detail view
- `components/Navigation.jsx` — add Fleet Map tab
- `package.json` — add `leaflet`, `react-leaflet`

---

## Demo Script (once built)

1. Open Dashboard → show current bridge status
2. Open a crack in Crack Detection → show growth chart: "this crack has grown 240% over 3 inspections"
3. Show prediction card: "reaches critical width in ~N days — inspect by [date]"
4. Switch to Fleet Map tab → show 3 Cairo bridges color-coded by risk, click one for details
5. Close with the one-line pitch: *"We don't just detect cracks — we track how they evolve and predict when they'll need attention, across an entire bridge fleet, running fully offline on low-cost hardware."*

---

## Open Items / Honest Gaps to Flag to Judges if Asked

- Prediction is a linear extrapolation, not a trained forecasting model — accurate framing, not hidden
- Growth chart demo data is staged/backdated, since real multi-week growth can't be observed live — say so if asked, frame as "simulating what continuous field deployment would show"
- Crack-to-crack linking uses simple bounding-box proximity, not persistent visual re-identification — fine for a demo/MVP, worth noting as a "v2" improvement if pressed
