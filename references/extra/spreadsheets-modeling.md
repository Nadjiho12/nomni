# Spreadsheet modeling (Excel, Google Sheets, LibreOffice)

*Last updated: 2026-10-17 | Version-sensitive: Excel/Sheets function availability (XLOOKUP, LET, dynamic arrays) | Re-check current docs before pinning versions, prices, or API names.*

Build models that other people can trust: structure, formulas, scenarios, checks, and verification by recalculation. Tool: `scripts/xlsx_model.py` (build a formula-driven forecast workbook, verify it against an independent Python model, scan any .xlsx for formula errors). If a dedicated spreadsheet-file skill or connector is available, use it for file creation and formatting, and use this reference for modeling method and verification.

## Contents
1. Model structure
2. Formatting and conventions
3. Formula toolkit
4. Scenarios and sensitivity
5. Checks and audit
6. Common errors
7. Python and openpyxl
8. Recalculation and verification (LibreOffice)
9. Charts and presentation
10. Sheets vs Excel differences
11. Verification

## 1. Model structure

Separate **inputs, calculations, outputs**:
- **Assumptions/Inputs sheet:** every changeable number once, with a label, unit, and source; blue font and a fill for input cells.
- **Calculation sheets:** formulas only, no typed numbers; one row = one concept, one column = one period; consistent formulas across a row (fill right) and down.
- **Outputs/Summary sheet:** key results, charts, and **checks**.
Time runs left to right (or top to bottom) consistently; one currency and unit per model; a "Notes" or README sheet with purpose, version, owner, and instructions. Prefer tables with named columns for data; avoid merged cells in data areas; avoid hidden sheets and volatile tricks.
`python scripts/xlsx_model.py build --out model.xlsx --new-per-month 20 --growth 0.05 --churn 0.05 --arpu 12 --gross-margin 0.85 --fixed 800 --cac 25 --cash 3000` produces this structure (Assumptions, Forecast, Summary with a reconciliation check).

## 2. Formatting and conventions

Blue = inputs, black = formulas, green = links to other sheets (common finance convention). Number formats with units (0.0%, #,##0, $#,##0.00); freeze panes on headers; column widths readable; consistent decimals; negative numbers visible; no color as the only signal. Name ranges for key inputs only when it improves clarity; avoid cryptic names.

## 3. Formula toolkit

| Task | Formulas |
|---|---|
| Lookup | `XLOOKUP(key, keys, values, "not found")` (Excel 365/Sheets), `INDEX(range, MATCH(key, keys, 0))` (everywhere) |
| Conditional sums | `SUMIFS(sum_range, crit_range1, crit1, crit_range2, crit2)`, `COUNTIFS`, `AVERAGEIFS` |
| Dates | `EOMONTH(start, n)`, `EDATE`, `DATEDIF`, `NETWORKDAYS`, `TEXT(date, "yyyy-mm")` |
| Finance | `NPV(rate, flows)` (flows start next period), `IRR`, `XNPV/XIRR` (dated), `PMT(rate, nper, pv)`, `FV`, `RATE` |
| Growth | `=B2*(1+g)^(n-1)`; CAGR `=(end/start)^(1/years)-1` |
| Logic | `IF`, `IFS`, `AND/OR`, `IFERROR(value, fallback)` (use sparingly: it can hide bugs) |
| Text/clean | `TRIM`, `CLEAN`, `LEFT/RIGHT/MID`, `TEXTSPLIT` (365), `SUBSTITUTE` |
| Arrays | `FILTER`, `SORT`, `UNIQUE`, `SEQUENCE`, `LET` (365); `SUMPRODUCT` for older versions |
| Stats | `AVERAGE`, `MEDIAN`, `STDEV.S`, `PERCENTILE.INC`, `CORREL`, `FORECAST.LINEAR` |
Absolute vs relative references: `$B$2` fixed, `B2` moves; mixed `$B2`/`B$2` for tables. Prefer one consistent formula per row. Avoid whole-column references in heavy models. Avoid volatile functions (`INDIRECT`, `OFFSET`, `TODAY`) in large models.

## 4. Scenarios and sensitivity

- **Scenario switch:** a selector cell (1=Base, 2=Pessimistic, 3=Optimistic) with `CHOOSE(selector, base, low, high)` or `INDEX` pulling the active inputs into the Assumptions sheet.
- **Sensitivity table:** vary 1-2 inputs across a grid and show an output (Excel Data Table, or compute the grid with formulas or a script). Always test churn, price, acquisition cost, and growth ±30%.
- **Break-even and runway** as explicit rows. Compare with `python scripts/biz_calc.py forecast ...` as an independent check.
- Document what each scenario means and who approved the assumptions.

## 5. Checks and audit

Add a **Checks** block that must read 0/TRUE: totals reconcile (ending cash = starting cash + sum of flows), balance sheet balances, percentages sum to 100%, no negative inventory, signs correct, lookups found. Cross-check with an independent calculation. Audit tools: Trace Precedents/Dependents, Evaluate Formula, Go To Special (formulas, constants), and a formula-consistency scan across rows. Protect formulas (sheet protection) but keep inputs editable. Keep a change log for important models.

## 6. Common errors

| Error / issue | Cause | Fix |
|---|---|---|
| `#DIV/0!` | Divide by zero/empty | Guard with `IF(den=0, 0, num/den)` only where zero is meaningful |
| `#REF!` | Deleted/moved cell | Rebuild reference; avoid deleting referenced rows |
| `#NAME?` | Misspelled function or name, unsupported function in the app | Fix spelling; check version support |
| `#VALUE!` | Text where number needed | Clean data (`VALUE`, `TRIM`), check number stored as text |
| `#N/A` | Lookup not found | Check keys, trailing spaces, exact-match flag |
| Wrong totals | Hard-coded numbers, inconsistent formulas, hidden rows, ranges missing rows | Formula audit; named tables; consistency check |
| Circular reference | Formula refers to itself | Restructure (use prior period); iterative calc only if intended |
| Slow workbook | Whole-column refs, volatile functions, huge arrays | Limit ranges; calculate in a database or script |
| Dates as text | Imported data | `DATEVALUE`, text-to-columns, set locale |
| Floating-point surprises | Binary arithmetic | `ROUND` at defined places (money to cents) |

## 7. Python and openpyxl

```python
# create a workbook with live formulas (openpyxl writes formulas but does not calculate them)
from openpyxl import Workbook
wb = Workbook()
ws = wb.active
ws.title = "Model"
ws.append(["Price", 25])
ws.append(["Units", 120])
ws.append(["Revenue", "=B1*B2"])
ws.append(["Check (should be 0)", "=B3-B1*B2"])
wb.save("tiny_model.xlsx")
print("saved with formulas:", [c.value for c in ws["B"]])
```
Notes: openpyxl stores formulas as text and leaves cached values empty until a spreadsheet application recalculates; `load_workbook(data_only=True)` reads cached values (None until recalculated). pandas `to_excel` writes values only. XlsxWriter creates new files with charts and formatting (cannot edit existing files). Keep the source of truth in code (a build script) so models are reproducible, and always verify by recalculating (section 8).

## 8. Recalculation and verification (LibreOffice)

LibreOffice headless can recalculate an .xlsx and save computed values, so scripts can verify formulas without Excel:
```
python scripts/xlsx_model.py verify model.xlsx     # recalculates, compares each Forecast cell to an independent Python model
python scripts/xlsx_model.py check any.xlsx        # recalculates and lists formula error cells
```
Under the hood: `soffice --headless --convert-to xlsx --outdir out file.xlsx`, then read with `openpyxl.load_workbook(out/file.xlsx, data_only=True)`. Use a private profile directory (`-env:UserInstallation=file:///tmp/profile`) to avoid lock conflicts. Excel and LibreOffice can differ on a few functions and on dynamic arrays: confirm the target application's support. Exit code 3 means LibreOffice or openpyxl is unavailable: then state the workbook is **open gap** and give the user a manual checklist (open, recalc with F9, check the Checks block).

## 9. Charts and presentation

One message per chart, labeled axes with units, start bar charts at zero, limited colors, titles that state the finding; build charts from calculated ranges so they update; put the key outputs and checks at the top of the Summary. For sharing: export a PDF of the Summary, lock formulas, and include a short "how to use" note.

## 10. Sheets vs Excel differences

Google Sheets: `ARRAYFORMULA`, `QUERY`, `IMPORTRANGE`, `GOOGLEFINANCE`; collaborative; slower with big data; no Data Tables (use formulas/Apps Script). Excel: Data Tables, Power Query, Power Pivot, VBA/Office Scripts, dynamic arrays (365). LibreOffice Calc: free; most core functions compatible; verify advanced Excel-only features. Avoid features unsupported by recipients.

## 11. Verification

Build or open the workbook, run `xlsx_model.py verify` or `check` (recalculated, zero error cells, reconciliation check 0, independent model matches), view key outputs, test a scenario change, and report **open gap** items (Excel-specific behavior if only LibreOffice was used, macros, external links).
