# Vietnam EVN TOU Tariff — 2024 vs 2026 Hour Mapping

**Effective date of new schedule:** April 22, 2026

This document is the canonical hour-by-hour reference for the Vietnam EVN
Time-of-Use tariff change. All model inputs (JSON `tariff_schedule` blocks and
Excel "Tariff Schedule" sheets) must be consistent with the tables below.

---

## Tariff Window Summary

| Attribute | Old (≤ April 21, 2026) | New (≥ April 22, 2026) |
|---|---|---|
| **Off-Peak (Mon–Sat)** | 22:00–04:00 | 00:00–06:00 |
| **Normal (Mon–Sat)** | 04:00–09:30, 11:30–17:00, 20:00–22:00 | 06:00–17:30, 22:30–24:00 |
| **Peak (Mon–Sat)** | 09:30–11:30 and 17:00–20:00 (2 blocks, 5 hrs) | 17:30–22:30 (1 block, 5 hrs) |
| **Sunday** | Normal: 04:00–22:00 / Off-Peak: 22:00–04:00 | Normal: 06:00–24:00 / Off-Peak: 00:00–06:00 |
| **BESS cycles/day** | 2 (morning + evening) | 1 (midnight charge → evening peak) |

---

## Whole-Hour Mapping Convention

The model operates on integer hours (0–23), where hour `h` covers the interval
`[h:00, h+1:00)`. Half-hour tariff boundaries are resolved as follows:

- **Peak start at X:30** → first Peak hour is `X+1` (the next full hour).
- **Peak end at X:30** → last Peak hour is `X` (the boundary falls within that hour, which is classified Peak since the majority of its economic value is Peak).

This convention preserves the total peak block duration (5 hrs old, 5 hrs new) in whole-hour arithmetic.

---

## Old Schedule (≤ April 21, 2026)

### Weekday (Monday–Saturday)

| Hour | Window | Period |
|------|--------|--------|
| 0 | 00:00–01:00 | off_peak |
| 1 | 01:00–02:00 | off_peak |
| 2 | 02:00–03:00 | off_peak |
| 3 | 03:00–04:00 | off_peak |
| 4 | 04:00–05:00 | standard |
| 5 | 05:00–06:00 | standard |
| 6 | 06:00–07:00 | standard |
| 7 | 07:00–08:00 | standard |
| 8 | 08:00–09:00 | standard |
| 9 | 09:00–10:00 | standard |
| 10 | 10:00–11:00 | **peak** |
| 11 | 11:00–12:00 | **peak** |
| 12 | 12:00–13:00 | standard |
| 13 | 13:00–14:00 | standard |
| 14 | 14:00–15:00 | standard |
| 15 | 15:00–16:00 | standard |
| 16 | 16:00–17:00 | standard |
| 17 | 17:00–18:00 | **peak** |
| 18 | 18:00–19:00 | **peak** |
| 19 | 19:00–20:00 | **peak** |
| 20 | 20:00–21:00 | standard |
| 21 | 21:00–22:00 | standard |
| 22 | 22:00–23:00 | off_peak |
| 23 | 23:00–24:00 | off_peak |

**Summary:** Off-Peak = {0,1,2,3,22,23} | Standard = {4,5,6,7,8,9,12,13,14,15,16,20,21} | Peak = {10,11,17,18,19}

### Sunday

| Hour | Period |
|------|--------|
| 0–3 | off_peak |
| 4–21 | standard |
| 22–23 | off_peak |

**Summary:** Off-Peak = {0,1,2,3,22,23} | Standard = {4,5,...,21} | Peak = {} (none)

---

## New Schedule (≥ April 22, 2026)

### Weekday (Monday–Saturday)

| Hour | Window | Period |
|------|--------|--------|
| 0 | 00:00–01:00 | off_peak |
| 1 | 01:00–02:00 | off_peak |
| 2 | 02:00–03:00 | off_peak |
| 3 | 03:00–04:00 | off_peak |
| 4 | 04:00–05:00 | off_peak |
| 5 | 05:00–06:00 | off_peak |
| 6 | 06:00–07:00 | standard |
| 7 | 07:00–08:00 | standard |
| 8 | 08:00–09:00 | standard |
| 9 | 09:00–10:00 | standard |
| 10 | 10:00–11:00 | standard |
| 11 | 11:00–12:00 | standard |
| 12 | 12:00–13:00 | standard |
| 13 | 13:00–14:00 | standard |
| 14 | 14:00–15:00 | standard |
| 15 | 15:00–16:00 | standard |
| 16 | 16:00–17:00 | standard |
| 17 | 17:00–18:00 | standard |
| 18 | 18:00–19:00 | **peak** |
| 19 | 19:00–20:00 | **peak** |
| 20 | 20:00–21:00 | **peak** |
| 21 | 21:00–22:00 | **peak** |
| 22 | 22:00–23:00 | **peak** |
| 23 | 23:00–24:00 | standard |

**Summary:** Off-Peak = {0,1,2,3,4,5} | Standard = {6,7,8,9,10,11,12,13,14,15,16,17,23} | Peak = {18,19,20,21,22}

### Sunday

| Hour | Period |
|------|--------|
| 0–5 | off_peak |
| 6–23 | standard |

**Summary:** Off-Peak = {0,1,2,3,4,5} | Standard = {6,7,...,23} | Peak = {} (none)

---

## Old vs New — Side-by-Side Comparison

| Hour | Old Period | New Period | Change |
|------|-----------|-----------|--------|
| 0 | off_peak | off_peak | — |
| 1 | off_peak | off_peak | — |
| 2 | off_peak | off_peak | — |
| 3 | off_peak | off_peak | — |
| 4 | standard | **off_peak** | ↓ downgraded |
| 5 | standard | **off_peak** | ↓ downgraded |
| 6 | standard | standard | — |
| 7 | standard | standard | — |
| 8 | standard | standard | — |
| 9 | standard | standard | — |
| 10 | **peak** | standard | ↓ downgraded |
| 11 | **peak** | standard | ↓ downgraded |
| 12 | standard | standard | — |
| 13 | standard | standard | — |
| 14 | standard | standard | — |
| 15 | standard | standard | — |
| 16 | standard | standard | — |
| 17 | **peak** | standard | ↓ downgraded |
| 18 | **peak** | **peak** | — |
| 19 | **peak** | **peak** | — |
| 20 | standard | **peak** | ↑ upgraded |
| 21 | standard | **peak** | ↑ upgraded |
| 22 | off_peak | **peak** | ↑ upgraded |
| 23 | off_peak | standard | ↑ upgraded |

**Net changes:**
- Hours 4–5: standard → off_peak (BESS charging window expands by 2 hrs)
- Hours 10–11: peak → standard (morning solar peak uplift eliminated)
- Hour 17: peak → standard (17:00–17:30 window removed; peak now starts at 17:30→18:00)
- Hours 20–21: standard → peak (evening peak extended 2 hrs later)
- Hour 22: off_peak → peak (old off-peak start absorbed into peak)
- Hour 23: off_peak → standard (late-night shift to standard before midnight)

---

## Key Revenue Implications

1. **Solar generation (06:00–17:30)** now falls entirely within Normal hours. The
   old morning peak window (10:00–12:00, hours 10–11) no longer overlaps with
   solar output — eliminating morning peak uplift revenue.

2. **BESS cycle reduction:** Only 1 off-peak window (00:00–06:00) precedes the
   single peak block (18:00–23:00). The old schedule had two charging windows
   enabling 2 cycles per day.

3. **Peak window shift:** BESS discharges 18:00–23:00 instead of two windows
   (10:00–12:00 and 17:00–20:00). The evening window is 2 hours longer, but the
   morning cycle is eliminated.

4. **Off-peak charging:** Shifts from 22:00–04:00 to 00:00–06:00 — 2 hours later
   start, avoids the 22:00–00:00 block that was previously off-peak (now peak).

---

## JSON `tariff_schedule` Block Format

The `tariff_schedule` object in project JSON files lists the integer hours (0–23)
assigned to each period. The model uses the `weekday` sub-object for all hours
(the physics engine handles Sunday behaviour separately via `is_sunday` flag).

**Old (TOU2024):**
```json
"tariff_schedule": {
  "version": "2024",
  "weekday": {
    "off_peak": [0, 1, 2, 3, 22, 23],
    "standard": [4, 5, 6, 7, 8, 9, 12, 13, 14, 15, 16, 20, 21],
    "peak": [10, 11, 17, 18, 19]
  }
}
```

**New (TOU2026):**
```json
"tariff_schedule": {
  "version": "2026",
  "weekday": {
    "off_peak": [0, 1, 2, 3, 4, 5],
    "standard": [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 23],
    "peak": [18, 19, 20, 21, 22]
  }
}
```

## Excel "Tariff Schedule" Sheet Format

The Excel sheet uses two columns: `hour` (0–23) and `period` (`off_peak` / `standard` / `peak`).
Duplicate the existing "Tariff Schedule" sheet as "Tariff Schedule 2026" and remap
the `period` column to match the new schedule above. Run `scripts/add_ecoplexus_tou2026_sheet.py`
to perform this update programmatically.
