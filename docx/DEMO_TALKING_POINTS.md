# Demo Talking Points — SensorX Challenge 2026

Use these lines when presenting to judges. They match what the system actually does.

---

## Prediction feature (Feature 2)

> **"This is a linear trend extrapolation from historical detections — not a trained ML forecasting model."**

Why say this: It is accurate, credible, and avoids overstating the AI. The backend computes `growth_per_day` from the first and last inspection in a crack's lineage, then estimates days until area reaches `CRITICAL_AREA_THRESHOLD` (10,500 px²).

---

## Growth chart demo data (Feature 1)

> **"The multi-week growth timeline uses staged backdated seed data, because real field growth cannot be observed in a live demo. In deployment, each inspection would append to the same crack lineage automatically."**

Seed crack: `CRK-CAIRO12-001` on Qasr El-Nile Bridge — 3 inspections over 21 days (area 1,500 → 3,420 → 8,060 px²).

---

## Crack linking (Feature 1)

> **"We link repeat detections using bounding-box proximity on the same bridge — a practical MVP. Production v2 would add visual re-identification across camera angles and lighting."**

---

## Fleet map (Feature 3)

> **"This is a fleet-level view: every bridge pinned on a map, colored by max crack severity, so engineers see where to send crews first."**

---

## Closing pitch (from plan.md)

> **"We don't just detect cracks — we track how they evolve and predict when they'll need attention, across an entire bridge fleet, running fully offline on low-cost hardware."**

---

## 3-minute demo script

1. **Dashboard** — show current bridge status and live sensors.
2. **Crack Detection → Tracked Cracks** — open **Demo lineage crack** (`CRK-CAIRO12-001`); show growth chart and "+X% since first detection".
3. **Prediction card** — show "~N days to critical size — inspect by [date]" (bilingual).
4. **Fleet Map tab** — 3 Cairo bridges, color-coded, click popup for details.
5. **Close** — use closing pitch above.
