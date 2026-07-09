# Road Pavement Crack Detection System — Enhancement Plan
**Adapted from bridge_crack_system**
**Date:** July 9, 2026

## Goal

Repurpose the existing crack-detection architecture (YOLOv8 + FastAPI/MySQL + React, upload-based) from single-bridge structural monitoring into a **standards-based road pavement condition platform**, by adding three features:

1. Multi-Class Distress Classification
2. PCI (Pavement Condition Index) Scoring
3. Road Network Risk Map (GIS)
4. *(Optional stretch)* A handful of low-effort enhancements — review queue reuse, EXIF GPS, repair-priority ranking, pothole headline metric, duplicate-detection guard

These are sequenced deliberately: #2 depends on #1's output (distress type + severity per detection). #3 depends on #2 (needs a per-segment score to color the map). #4 items are independent add-ons, tackled only if time allows. No new hardware is introduced — this stays upload-based, same as the bridge system's core flow.

---

## What carries over vs. what changes

| Component | Bridge system | Road system |
|---|---|---|
| Capture method | Uploaded photos | Uploaded photos (same) |
| Backend/DB | FastAPI + MySQL | Reused as-is |
| Frontend | React, bilingual EN/AR | Reused as-is |
| Detection model | YOLOv8, single class ("crack") | YOLOv8, **already trained** on multiple road classes (cracks, potholes, manholes) — no retraining needed |
| Scoring | Custom `severity_level` (1–3) | **ASTM D6433-inspired PCI** (0–100, standards-referenced) |
| Physical sensors | MPU6050, DS18B20, HX711 strain gauge | **Dropped** — not applicable to image-only pavement assessment |
| Entity | `bridges` table, one structure per record | `road_segments` table, a stretch of road per record |
| Map | Points (bridge locations) | Points or short polylines (road segment locations) |

**This is the single biggest change from the original plan**: since the model already detects cracks, potholes, and manholes, Feature 1 is no longer a training/data problem — it's a schema + severity-logic problem. The build order and effort estimates below reflect that.

---

## Why these three

| Feature | Uses existing pipeline? | New concept for judges | Effort |
|---|---|---|---|
| Distress classification & severity | Yes (model already trained; this is schema/logic work) | "We identify *what kind* of damage and how severe, not just that damage exists" | Low |
| PCI scoring | Yes (built on #1's classified detections) | "We report a real industry-standard score municipalities already use" | Low–Medium |
| Risk map | Partial (reuse bridge Feature 3 map pattern) | "Fleet-level view of an entire road network, not one photo at a time" | Low |

---

## Feature 1: Distress Classification & Severity Logic

**Objective:** Since the model already detects multiple classes (cracks, potholes, manholes), the work here isn't training — it's turning raw class labels into ASTM D6433-style distress types with severity, since PCI scoring (Feature 2) needs both.

**Scope decision:** Map your existing model classes onto ASTM-recognized distress categories where they align:
- Cracks → sub-classify by shape/geometry if your model's bounding box + aspect ratio can distinguish patterns (e.g., wide interconnected regions ≈ alligator cracking; single long thin boxes ≈ longitudinal/transverse) — **or**, if the model only outputs a generic "crack" class, keep it as one category and be upfront that sub-typing isn't implemented (simpler, still honest)
- Potholes → maps directly to ASTM's Potholes (AC-13), measured by count
- Manholes → not an ASTM distress type itself, but relevant as a **context flag**: cracking or subsidence *around* a manhole is a distinct distress (utility cut patching / settlement) worth flagging separately, so don't just ignore this class — decide whether to (a) treat manholes as a landmark/reference feature on the map only, or (b) flag "crack near manhole" as a higher-severity condition since utility trenches are common failure points

### Backend Tasks
- [ ] Update `detect/{segment_id}/save` to store `distress_type` (from existing model classes, possibly sub-typed for cracks) and `severity_level` (Low/Medium/High) per detection
- [ ] Add severity-mapping logic based on bounding box size / area thresholds per class (ASTM's severity criteria are qualitative — define your own width/area cutoffs and state clearly these are your own calibration, not ASTM's literal tables)
- [ ] Decide and implement the manhole-proximity rule from the scope decision above (even a simple "flag if crack detection overlaps/borders a manhole detection" is enough for a demo)

### Frontend Tasks
- [ ] Update detection result view to show distress type + severity as a labeled tag (bilingual EN/AR), reusing the existing detection card UI from `CrackDetection.jsx`
- [ ] If implementing the manhole-proximity flag, surface it as a visible warning badge on affected detections

### Definition of Done
Uploading a road photo returns bounding boxes each labeled with a distress type and Low/Medium/High severity — not just a raw class name — and manhole-adjacent damage is distinguishable from mid-segment damage.

---

## Feature 2: PCI (Pavement Condition Index) Scoring

**Objective:** Convert raw detections into a standards-referenced 0–100 condition score per road segment, so the output is something a municipal engineer would recognize rather than an arbitrary in-house number.

### Backend Tasks
- [ ] Define a **simplified deduct-value model**: for each distress type + severity, assign an approximate deduct value (informed by, but not a literal reproduction of, ASTM's nonlinear deduct curves — those require licensed tables and a full density/curve lookup that's out of scope)
- [ ] Add `GET /segment/{segment_id}/pci` endpoint
  - Aggregates all distresses recorded for a segment
  - Computes total deducts, subtracts from 100, clamps at 0
  - Maps score to a condition category: Good (86–100) / Satisfactory (71–85) / Fair (56–70) / Poor (41–55) / Very Poor (26–40) / Failed (0–25)
  - Returns bilingual message strings + category

### Frontend Tasks
- [ ] Add a "Condition Score" card to the segment detail view: large PCI number, category label, color-coded (green→red), reusing existing `--warning-color`/`--danger-color` variables

### Framing for Judges
- [ ] Explicit talking point: *"Our PCI score is inspired by ASTM D6433's methodology — same category thresholds and same idea of distress-type/severity-weighted deducts — but our deduct values are our own calibration, not a reproduction of the licensed ASTM curves."* This is the honest version of the framing that worked well for the bridge project's prediction feature.

### Definition of Done
A processed road segment shows a single PCI number (0–100) and condition category derived from its detected distresses.

---

## Feature 3: Road Network Risk Map (GIS)

**Objective:** Fleet-level view of multiple road segments, pinned on a map, colored by PCI category — same pattern as the bridge system's map feature, retargeted to roads.

### Database Tasks
- [ ] Add `latitude`, `longitude` (or start/end coordinates if you want line segments) to `road_segments` table
- [ ] Seed 3+ real Cairo-area road segments with coordinates

### Backend Tasks
- [ ] Add `GET /segments/map` endpoint — for each segment: PCI score, condition category, distress count, coordinates. Single call powers the whole map.

### Frontend Tasks
- [ ] Reuse `leaflet` / `react-leaflet` setup from the bridge project's `BridgeMap.jsx` as a base — rename/adapt to `RoadMap.jsx`
- [ ] `CircleMarker` (or `Polyline` if using start/end points) per segment, colored by PCI category
- [ ] Popup on click: segment name, PCI score, category, distress count (bilingual)

### Definition of Done
A map tab shows 3+ Cairo road segments pinned, colored by current PCI category, clickable for summary info.

---

## Feature 4 (Optional): Low-Effort, High-Payoff Enhancements

None of these are required for the core three features to work, but each reuses something already built and meaningfully strengthens the demo. Treat as stretch goals if Days 1–3 finish on schedule.

### 4a. Reuse the human-in-the-loop review queue
The bridge system already has a low-confidence review queue for crack detections. Road photos have the same problem — potholes and manholes at odd angles or in shadow are easy to misclassify. Route low-confidence road detections through the same queue rather than building a new one.
- [ ] Extend the existing review-queue logic to cover the new distress types, not just cracks

### 4b. Auto-extract GPS from photo EXIF data
Uploaded phone photos typically carry GPS coordinates in EXIF metadata. Reading this on upload avoids manually entering segment coordinates and makes the map feel like a real deployment rather than staged demo data.
- [ ] On upload, attempt to read EXIF GPS tags; fall back to manual entry if absent (many phones strip EXIF on share/compression, so this needs a graceful fallback)
- [ ] Populate `road_segments.latitude/longitude` automatically when available

### 4c. Repair-priority ranking (not just a score)
A PCI number tells you how bad a segment is, not what to fix first across a network with limited budget. Turn the map/list into an actionable tool:
- [ ] Add `GET /segments/priority` — segments sorted by ascending PCI (worst first); optionally let the user weight by a manually-assigned "traffic importance" field per segment
- [ ] Show this as a simple ranked table alongside the map — "Repair queue: 1) Nasr Road (PCI 32) 2) ..."
- This reframes the pitch from "we show you problems" to "we tell you where to send the crew first" — a stronger closing line for judges

### 4d. Surface pothole count as its own headline metric
PCI is an aggregate score that non-technical judges won't intuitively read. Pothole count is instantly understandable ("this segment has 12 potholes") and disproportionately drives PCI down anyway.
- [ ] Add a distinct "Pothole Count" stat next to the PCI card on the segment detail view, pulled straight from Feature 1's stored detections (no new endpoint needed — just surface an existing count)

### 4e. Basic duplicate-detection guard
If a road segment gets multiple uploaded photos over time (or overlapping shots of the same stretch), the same pothole/manhole could get counted more than once, inflating deducts unfairly.
- [ ] Simple rule: when saving a new detection, check for an existing detection of the same class within a small bounding-box distance on the same segment; if found, treat as a duplicate/update rather than a new count
- Worth doing even in a minimal form — an inflated pothole count is the kind of thing a sharp judge will probe on

### What I'd skip
Time-series crack growth tracking (like the bridge project's original Feature 1) isn't worth porting here unless you actually have repeat photos of the same segment over time — without real repeat data it just becomes another "this is staged" caveat to manage, and you already have a few of those (PCI calibration, distress-type mapping) to keep track of. Better to keep the honest-gaps list short and defensible than to add a feature that invites more questions than it answers.

---

## Build Order

```
Day 1 (AM):  Feature 1 — severity-mapping logic, manhole-proximity rule,
             update save endpoint + detection UI
Day 1 (PM):  Feature 2 backend — deduct-value model + /segment/{id}/pci endpoint
Day 2 (AM):  Feature 2 frontend — condition score card
Day 2 (PM):  Feature 3 backend — migration + /segments/map endpoint
             (parallelizable with Day 1–2 if a second person is available)
Day 3 (AM):  Feature 3 frontend — map component (adapt bridge map code) + nav tab
Day 3 (PM):  End-to-end test, fix edge cases, rehearse demo

Day 4 (if time allows — stretch goals from Feature 4, roughly in payoff order):
             EXIF GPS auto-extract → pothole headline metric → repair-priority
             ranking → duplicate-detection guard → review-queue reuse
```

With the model already trained on the needed classes, all three features are now mostly schema, scoring-logic, and UI work reusing patterns already built for the bridge system — no feature here is a hard bottleneck the way retraining would have been. If short on time, prioritize: **Feature 1 → Feature 2 → Feature 3**, since #2 and #3 depend on #1's output.

---

## File Checklist

**New files**
- `backend/pci_scoring.py`
- `components/RoadMap.jsx` (adapted from `BridgeMap.jsx`)

**Modified files**
- `backend/main.py` — update save endpoint for `distress_type`/severity; add `/segment/{id}/pci`, `/segments/map`; add `/segments/priority` if doing 4c
- `backend/models.py` — rename/adapt `Bridge` → `RoadSegment`, add `latitude`/`longitude`
- `components/CrackDetection.jsx` — show distress type + severity tags, add PCI card, add pothole count stat (4d)
- `components/Navigation.jsx` — relabel Fleet Map tab for roads

**Optional (Feature 4)**
- `backend/exif_gps.py` — EXIF GPS extraction on upload (4b)
- `backend/duplicate_guard.py` — bounding-box proximity dedup check (4e)
- Existing review-queue module — extend to cover new distress types (4a)

---

## Demo Script (once built)

1. Upload a road photo → show detection with specific distress type + severity labels ("alligator cracking, medium severity") and the pothole count stat if built (4d)
2. Show the PCI card: "Segment condition score: 58 — Fair"
3. Explain briefly: "This mirrors ASTM D6433, the standard municipalities use for pavement management, with our own calibrated deduct values"
4. Switch to Road Map tab → show 3+ Cairo segments color-coded by condition, click one for details
5. If built, show the repair-priority ranking (4c): "Here's the queue — this tells the maintenance team where to send a crew first, not just where problems exist"
6. Close with the one-line pitch: *"We don't just flag that a road has a crack — we classify the damage type, score it against a real industry standard, and rank the whole network by what needs attention first."*

---

## Open Items / Honest Gaps to Flag to Judges if Asked

- PCI is ASTM D6433-*inspired*, not a certified/licensed implementation — deduct values are your own calibration, stated explicitly
- Severity thresholds (Low/Medium/High width or area cutoffs) are your own calibration, since ASTM's criteria are qualitative and the full deduct curves require licensed tables
- Model classes (cracks, potholes, manholes) don't map one-to-one onto ASTM's 19 distress types — this is a deliberate simplification, not full standard coverage; worth naming as a "v2" scope expansion if pressed
- Manhole handling (context flag vs. landmark-only) is a judgment call you're making, not a documented industry convention — be ready to explain your reasoning if asked
