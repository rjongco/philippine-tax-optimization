# Payroll Structure App

Implements the model documented in [`PAYROLL_MODEL.md`](../PAYROLL_MODEL.md).
Design notes: [`docs/superpowers/specs/2026-08-05-payroll-app-design.md`](../docs/superpowers/specs/2026-08-05-payroll-app-design.md).

**Where this app and `PAYROLL_MODEL.md` disagree, the document is right and the app has a bug.**

## Running it

Two processes. Backend first — the frontend is useless without it, since every
number on screen comes from `/api/compute`.

```bash
cd backend && .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
```

```bash
npm run dev --prefix frontend
```

Then open http://localhost:5173. Vite proxies `/api` to port 8000, so there is no
CORS to configure locally.

API docs are at http://localhost:8000/docs.

## Tests

```bash
cd backend && .venv/Scripts/python.exe -m pytest
```

107 tests. The one that matters is `test_golden.py`: it replays all 16 employees
against values extracted from the verified workbook, 24 fields each, to the
centavo. **If it fails, nothing else in the app can be trusted** — fix the engine
before looking at anything the UI is doing.

`tests/golden.json` is the fixture, generated from `COMPUTATIONS.xlsx` after a full
Excel recalculation. Regenerate it only when the workbook itself is deliberately
changed.

## Excel export

The **Export to Excel** button on the breakdown page downloads a live workbook laid
out like the **`Sheet8`** tab — a *payroll register*, not the `Optimized Structure`
model. Deductions carried as negatives, `NET PAY = NON TAXABLE + NET TAXABLE +
WITHHOLDING`, same navy header, same Arial, same money format.

Three sheets: `Payroll Register` (columns A–O, Sheet8's shape; Q–AA derive the
withholding so the figure can be checked), `Reference` (de minimis schedule,
parameters, TRAIN table), and `SSS` (the lookup target).

Two deliberate departures from Sheet8, both forced by the model:

1. A **`PRODUCTIVITY INCENTIVE`** column is inserted after `DE MINIMIS`. The model
   has three pay components where Sheet8 had two, and the incentive cannot be folded
   into de minimis — different exemption tiers, different rules. `NON TAXABLE` is
   de minimis + incentive.
2. Sheet8's employee rows compute `NET PAY` as `WITHHOLDING/2`, which is half the tax
   rather than net pay; its own example rows use `SUM(K:M)`. The examples are right,
   so the export follows those.

`ABSENT/UNDERTIME/LATE` and `OVERTIME` ship blank and editable, so the file is usable
for an actual payroll run. Both flow into `GROSS TAXABLE`; absences also reduce the
PhilHealth base, as in Sheet8.

**It carries formulas, not baked numbers.** A spreadsheet of frozen literals is a
screenshot — you cannot change a salary in it and see the effect, which is the main
reason anyone opens the file. Blue cells are editable inputs; everything else is a
formula.

That means the model exists twice: once in Python, once as Excel formulas. The risk
of the two drifting is handled by `tests/test_export.py::test_excel_formulas_agree_with_the_engine`,
which generates a workbook, recalculates it through Excel, and compares every cell
against the engine. **Do not weaken that test** — it is the only thing standing
between the export and a silent divergence.

The recalculation tests need Excel and skip cleanly where it is unavailable
(LibreOffice, which the `xlsx` skill's `recalc.py` drives, is not installed here).
The structural tests — formulas present, no spilling array functions, headers
correct — run everywhere.

Export reflects **what is on screen, including unsaved edits**, since the file is
built from the scenario in the request body rather than from storage.

## Layout

```
backend/app/engine/     the model. Pure Python, no framework imports, no I/O.
backend/app/routers/    HTTP surface
backend/app/store.py    JSON persistence, one scenario
backend/app/docs_meta.py  per-parameter documentation shown on the config page
frontend/src/pages/     the four screens
frontend/src/api/       typed client
```

`engine/` is importable and testable with no server running. That boundary is
deliberate — keep it.

## Two rules

**1. The computation lives in Python, once.** Never mirror it in TypeScript for
"instant" feedback. A second implementation drifts from the first, and the
divergence surfaces in a payslip months later. The frontend renders what the API
returns.

**2. No `float` in the engine.** Everything is `Decimal`, constructed from strings.
Rounding happens exactly once, at the API boundary (`schemas.out`), except in
`engine/schedule.py` where the cash view legitimately quantizes to centavos
because a repeating decimal cannot be paid.

## Accrual vs cash

The breakdown page is an **accrual** view: what each component is worth per month.
The payout schedule is a **cash** view: what leaves the bank on a date. They are
different objects. The schedule is computed, not derived by dividing by two —
see the module docstring in `engine/schedule.py` for why.

## Data

`backend/data/scenario.json` holds the current scenario. Decimals are stored as
strings so a save/load round trip cannot lose precision. Delete the file, or hit
Reset in the UI, to restore the seeded workbook values.

## Known caveats carried from the model

- `min_wage_daily` and `working_days` are **unverified placeholders**. They drive
  the minimum-wage floor check, which is meaningless until they are confirmed.
- The **Christmas gift** paid as monthly cash is the weakest line on the de minimis
  schedule (~₱10,800/yr exposure), retained by client decision. The config page
  carries the risk note.
- The **productivity incentive** needs a real monthly determination to survive
  reclassification. The app computes the amount; it cannot evidence the
  determination. That has to happen in the payroll process.
