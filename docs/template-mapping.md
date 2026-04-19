# Template Mapping — `Dienstzeitblatt_template.xlsx`

Source: `data/Dienstzeitblatt_template.xlsx` (inspected 2026-04-19)

## Sheet

- Single sheet: **`Tabelle1`**
- Used range: `A1:K45`
- Merged: `B5:I5` (header "Geleistete Dienstzeit")

## Cell map

### Header (written per export)

| Cell | Content | Notes |
|---|---|---|
| `A1` | `Dienstzeitblatt für Monat: {Monatsname}` | `{Monatsname}` = German month (Januar…Dezember) |
| `G1` | `Jahr:` | - |
| `H1` | `{year}` (int) | e.g. `2026` |

### Name (not touched)

| Cell | Content | Notes |
|---|---|---|
| `A3` | `Name: <NAME>` | fixed in template, leave as-is |

### Day rows (7–37 = days 1–31)

Row number for day **N** = **`N + 6`** (day 1 → row 7, day 31 → row 37).

The template supports **up to 4 session pairs per day**:

| Session | Start col (`von`) | End col (`bis`) |
|---|---|---|
| 1 | **B** | **C** |
| 2 | D | E |
| 3 | F | G |
| 4 | H | I |

- Write Python `datetime.time(h, m)` values → Excel stores them as time serials so the `C - B` subtraction in column J evaluates correctly.
- For months with < 31 days, leave extra rows empty (day-31 row in April stays blank).
- **Known template quirk:** the J-column formula only subtracts `C - B` (session 1). Sessions 2–4 are tracked visually but NOT added to the daily total. That's how the template is built — we do not patch it. If she consistently uses multiple sessions, she should fix the template (or we raise it as a v2 item).

### Formula cells (NEVER overwrite)

| Range | Formula |
|---|---|
| `J7:J37` | `=IF($B{n}<>"",$C{n}-$B{n},"")` — per-day hours |
| `K7:K37` | `=IF($B{n}<>"","Busaufsicht Flossing","")` — task label |
| `J38` | `=SUM(J7:J37)` — month total |

### Footer (not touched by v1)

| Cell | Content | Notes |
|---|---|---|
| `A38` | `Sollstunden im Monat:` | label |
| `D38` | `_______________` | she fills by hand |
| `G38` | `Summe geleistete Stunden:` | label (J38 has the sum formula) |
| `A40` | `Übertrag aus Vormonat:` | label |
| `D40` | `_______________` | by hand |
| `G40` | `abzgl. Sollstunden im Monat: _____` | by hand |
| `G42` | `Übertrag in den nächsten Monat: ___` | by hand |
| `G44` | `Unterschrift: _______________` | signature line |

## Data model → cell mapping (what `excel.py` does)

Input: list of `TimeEntry` rows filtered to `year=Y, month=M`, each with `date, start, end`.

Algorithm:

```
1. Load template workbook (keep_vba=False).
2. Set A1 = f"Dienstzeitblatt für Monat: {GERMAN_MONTHS[M]}"
3. Set G1 = "Jahr:"
4. Set H1 = Y  (int)
5. Group entries by day-of-month. Within a day, sort by start.
6. For each (day_of_month, sessions):
     row = day_of_month + 6
     for idx, session in enumerate(sessions[:4]):
         start_col, end_col = [("B","C"),("D","E"),("F","G"),("H","I")][idx]
         ws[f"{start_col}{row}"] = session.start  # datetime.time
         ws[f"{end_col}{row}"]   = session.end    # datetime.time
     if len(sessions) > 4:
         log.warning("day %s has %d sessions, template supports 4", day, len(sessions))
7. Save to data/exports/{Y}-{M:02d}.xlsx.
```

## German month names

```python
GERMAN_MONTHS = {
    1: "Januar", 2: "Februar", 3: "März", 4: "April",
    5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
    9: "September", 10: "Oktober", 11: "November", 12: "Dezember",
}
```

## Test fixture expectations

`tests/test_excel.py` should assert, after filling with e.g. `[(date(2026,4,1), time(8,0), time(12,30))]`:
- `ws["B7"].value == time(8, 0)`
- `ws["C7"].value == time(12, 30)`
- `ws["J7"].value` starts with `"=IF("` (formula untouched)
- `ws["A1"].value == "Dienstzeitblatt für Monat: April"`
- `ws["H1"].value == 2026`
