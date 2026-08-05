# Payroll Tax Optimization Model — AI Context Reference

**Subject file:** `COMPUTATIONS.xlsx`
**Primary tab:** `Optimized Structure`
**Jurisdiction:** Philippines (BIR / DOLE / SSS / PhilHealth / Pag-IBIG)
**Last verified:** 2026-08-05 — Excel full rebuild, 0 error cells, `AC60` = 70,465.10

This document is written for machine consumption. It states the model, its algebra, its
invariants, and its failure modes. Read this before modifying `COMPUTATIONS.xlsx`.

---

## 1. What the model does

Splits an employee's **already-agreed monthly gross salary** into three components so that the
maximum legal portion is exempt from income tax. No additional money is paid. No payment date
is added. Monthly take-home is unchanged.

```
signed monthly gross (G)
  ├── de minimis            (D)  → Tier 1 exempt, uncapped by the 90k ceiling
  ├── productivity incentive(A)  → Tier 2 exempt, consumes the 90k ceiling
  └── taxable basic salary  (B)  → taxable compensation
```

**Result:** every restructured employee reaches exactly **PHP 141,600/year exempt**
(= 51,600 de minimis + 90,000 benefits ceiling). This is the mathematical ceiling under
Philippine law. It cannot be exceeded without paying additional money.

**Measured effect:** PHP 70,465.10/year total tax saved across 16 employees, at zero
incremental company cost.

---

## 2. Core concept — the two exemption tiers

This is the single most important thing to understand. Conflating these tiers produces
wrong answers.

| | **Tier 1 — De minimis** | **Tier 2 — 13th month & other benefits** |
|---|---|---|
| Authority | RR 5-2011 as amended by RR 11-2018 | NIRC Sec. 32(B)(7)(e) |
| Cap | Per-item peso caps, absolute | **PHP 90,000/yr, combined** |
| Consumes the 90k? | **No** | **Yes — this IS the 90k** |
| Scales with salary? | **No** — fixed peso amounts | Yes (13th month = 1 month basic) |
| Above the cap | Excess falls into **Tier 2** | Becomes **taxable compensation** |
| BIR 2316 line | "De Minimis Benefits" | "13th Month Pay and Other Benefits" |
| Conditionality required? | **No** — flat and unconditional by nature | **Yes** — see §10 |

**Ordering rule:** fill Tier 1 to its caps first. Tier 1 is free space that does not touch
Tier 2. Only after Tier 1 is maxed should anything land in Tier 2.

**Anti-pattern:** granting de minimis *above* cap. The excess does not stay in Tier 1 — it
drops into Tier 2 and consumes the 90k anyway, while also reducing basic salary. Cost incurred,
no exemption gained. The legacy `de minimis` tab does exactly this (7,399.66/mo vs 4,300 cap).

---

## 3. Workbook map

| Sheet | Role | State |
|---|---|---|
| `Optimized Structure` | **The model.** All new work lives here. | Live formulas, verified |
| `Sheet8` | Legacy per-employee computation | Superseded; retained for comparison |
| `Sheet9` | SSS contribution table (2025 schedule, 15% / 5% EE, MSC 5k–35k) | Reference; model looks up against it |
| `de minimis` | Legacy de minimis schedule, 7,399.66/mo | **Over cap.** Superseded by §5 below |
| `05_2026` | Original payroll register (hidden) | **Broken — 456 `#REF!` cells.** Pre-existing, not caused by this model |

`Sheet9` known data errors (do not rely on column B): `B56` = 20249.99 (should be 30249.99);
`B66` = 34750 (zero-width top bracket). The model matches on **column A only**, which is
clean and monotonic, so these errors do not affect it.

---

## 4. Tab layout — `Optimized Structure`

| Rows | Section |
|---|---|
| 1–3 | Title and constraint statement |
| 5–9 | Legend (blue = input, black = formula, green = cross-sheet, yellow = assumption) |
| 11–19 | §1 De minimis schedule. **Total at `C19`** |
| 21–31 | §2 Parameters. **All model levers live here** |
| 33–40 | §3 TRAIN annual tax table. Lookup range `A35:D40` |
| 42–60 | §4 Employee computation. Header row 43, data **rows 44–59**, total row 60 |
| 61–63 | Notes on the 2316 mapping and exclusions |
| 65–71 | §5 Consultants — 8% gross receipts election |
| 73–81 | §6 Operating caveats |

Freeze pane is `C1` — **columns only, zero frozen rows**. Do not set a row freeze; a prior
value of `C44` froze 43 rows and made the sheet unscrollable.

---

## 5. De minimis schedule (Tier 1) — rows 13–19

All six are at statutory cap. Total `C19` = **4,300.00/month = 51,600/year**.

| Row | Item | /mo | /yr | Condition |
|---|---|---|---|---|
| 13 | Rice subsidy | 2,000.00 | 24,000 | Cash expressly allowed |
| 14 | Uniform and clothing | 500.00 | 6,000 | — |
| 15 | Laundry | 300.00 | 3,600 | — |
| 16 | Medical cash allowance, dependents | 250.00 | 3,000 | PHP 1,500/semester |
| 17 | Medicine / maintenance | 833.33 | 10,000 | **Monthly cash + annual substantiation** |
| 18 | Christmas gift | 416.67 | 5,000 | **Monthly cash — weakest item, see below** |
| **19** | **TOTAL** | **4,300.00** | **51,600** | |

**Deliberately excluded — do not add back:**

- **Employee achievement award (PHP 10,000/yr).** RR 5-2011 requires *tangible personal
  property other than cash or gift certificate*. Cash does not make it a weaker de minimis;
  it makes it **not one**. Available only as an actual non-cash award under a written
  non-discriminatory plan.
- **CBA / productivity incentive de minimis (PHP 10,000/yr).** Requires an actual CBA or a
  registered productivity scheme.
- **Leave monetization (max 10 days).** Legitimate Tier 1 item that does **not** consume the
  90k. Excluded only because paying it requires either its own date or the 13th-month run.
  Worth ~PHP 44,001/yr if activated. Requires a written VL policy and actual unused credits.
- **OT / night-shift meal allowance.** 25% of the regional minimum wage, per day, on actual
  OT or night-shift days only. Not a flat monthly entitlement.

**Item 17 (medicine) — policy: scheduled monthly cash with annual substantiation.** Receipts or
a signed declaration covering the PHP 10,000, collected each December alongside the 13th-month
run. The regulation's word is *actual* — an **evidentiary** test, not a timing test — so monthly
cash paid against evidence on file satisfies it. Nothing in RR 5-2011 requires payment timing to
match expense timing. Without substantiation the item fails Tier 1, drops into Tier 2 (already
full), and becomes fully taxable.

**Item 18 (Christmas gift) is the weakest line on the schedule. Retained by client decision.**
Two defects, and unlike item 17 **no substantiation cures either**:

1. A *gift* is gratuitous by definition. This one is carved out of contracted gross, so the
   employee was entitled to the money regardless — that is consideration for labour, not a gift.
2. RR 5-2011 says "gifts given during **Christmas**." That is an occasion test, and monthly
   release does not meet it.

Every other item on the schedule is an **allowance**, which carries no gratuity requirement, so
funding those out of gross is unremarkable. This one is different. Exposure if reclassified is
roughly **PHP 10,800/yr** across the group.

The compliant alternative is a single PHP 5,000 payment on the existing December 13th-month
date — no new payment date required — at a cost of PHP 416.67/mo in monthly cash. Both options
were presented with numbers; the client chose monthly cash. Do not silently "correct" this.

**Useful diagnostic:** *is this carved from money already owed?* The allowances pass it. The
gift does not. The productivity incentive passes **only if** the conditionality in §10 is real.

---

## 6. Parameters — `B22:B31`

| Cell | Parameter | Value | Type |
|---|---|---|---|
| `B22` | PhilHealth employee rate | 0.025 | fact (5% shared equally) |
| `B23` | PhilHealth salary floor | 10,000 | fact |
| `B24` | PhilHealth salary ceiling | 100,000 | fact |
| `B25` | Pag-IBIG employee share | 200 | fact (2% of 10,000 ceiling) |
| `B26` | Benefits exclusion ceiling | 90,000 | fact (NIRC 32(B)(7)(e)) |
| `B27` | Cash anchor — carve-out /mo | 5,300 | **model lever** |
| `B28` | Award — baseline comparison only | 1,000 | **not read by the live model** |
| `B29` | Minimum wage, daily | 695 | **ASSUMPTION — VERIFY** |
| `B30` | Working days divisor | 261 | **ASSUMPTION — VERIFY** |
| `B31` | Minimum basic /mo (floor) | 15,116.25 | `=B29*B30/12` |

**`B27` (cash anchor) is the most consequential cell.** It sets the 13th-month-date payment
via `F = G − B27`, which fixes total annual cash. Changing it changes every employee's total
compensation. It is currently set to preserve the prior structure's cash exactly.

**`B27` also defines hold-harmless.** Employees marked `No` receive `A = B27 − C19`, which forces
`E + G = B27` and therefore `H = D − B27` — exactly the baseline. `B27` = 5,300 originally because
it equalled de minimis 4,300 + award 1,000; that arithmetic coincidence is no longer relied on.

**`B28` is now baseline-only.** It feeds columns W–AB (the "before" case) and nothing else. It was
formerly hardcoded into column G's `No` branch, which silently taxed the four `No` employees the
moment the de minimis schedule changed. Do not reintroduce it into column G.

**`B29`/`B30` are placeholders.** 695/day at a 261-day (5-day week) divisor. Verify against
the wage order in force and the actual working-day divisor. Use 313 for a 6-day week. These
two cells drive the floor that prevents the optimizer pushing anyone below minimum wage.

---

## 7. The optimization algebra

Notation: `G` signed monthly gross, `D` de minimis, `P` 13th-month-date payment,
`A` productivity incentive, `B` taxable basic, `C` = ceiling (90,000).

```
D = 4,300                       (constant, Tier 1 at cap)
P = G − 5,300                   (cash anchor; fixes total annual cash)
B = G − D − A                   (residual)

INVARIANT 1  monthly payment = D + A + B = G          take-home unchanged
INVARIANT 2  annual cash     = 12G + P                total cash unchanged
INVARIANT 3  bucket          = 12A + P                Tier 2 consumption
```

Three constraints bound `A`:

```
(i)   12A + P ≤ C          bucket must not exceed 90,000   →  A ≤ (C − P)/12
(ii)  P ≥ B                13th-mo payment must cover the
                           statutory 13th month (= B)       →  A ≥ G − D − P
(iii) B ≥ floor            minimum wage                     →  A ≤ G − D − floor
```

Solved form, implemented verbatim in column G:

```
A = MIN( MAX( G−D−P , (C−P)/12 , 0 ) , MAX( 0 , G−D−floor ) )
```

Constraint (ii) is the binding one for high earners; (i) for everyone else; (iii) is a safety
stop that has not yet bound for any current employee.

**Why every restructured employee lands on 141,600:**

```
exempt = 12D + MIN(bucket, C)
       = 51,600 + 90,000
       = 141,600
```

This holds whether the bucket lands exactly on 90,000 (constraint i binding) or overshoots
(Garcia — the excess becomes spill and is taxed, so capped exempt is still 90,000).

---

## 8. Column reference — row 44 is the template

Every row 44–59 is identical in form. Absolute refs point at parameters; relative refs at the row.

| Col | Header | Formula |
|---|---|---|
| C | Restr? | input `Yes`/`No` |
| D | Signed gross /mo | input |
| E | De minimis /mo | `=$C$19` |
| F | 13th-mo date pay | `=D44-$B$27` |
| G | **Productivity incentive /mo** | `=IF(C44="No",($B$27-$C$19),MIN(MAX(D44-E44-F44,($B$26-F44)/12,0),MAX(0,D44-E44-$B$31)))` |
| H | Taxable basic /mo | `=D44-E44-G44` |
| I | Daily rate | `=H44*12/$B$30` |
| J | Min wage | `=IF(I44>=$B$29,"OK","BREACH")` |
| K | SSS EE | `=INDEX(Sheet9!$L$6:$L$66,MATCH(D44-E44,Sheet9!$A$6:$A$66,1))` |
| L | PhilHealth EE | `=MIN(MAX(H44,$B$23),$B$24)*$B$22` |
| M | Pag-IBIG EE | `=$B$25` |
| N | Net taxable /mo | `=H44-K44-L44-M44` |
| O | Bucket /yr | `=G44*12+F44` |
| P | Spill /yr | `=MAX(0,O44-$B$26)` |
| Q | Annual taxable | `=N44*12+P44` |
| R | Annual tax | `INDEX/MATCH` over `A35:D40` — see §9 |
| S | W/tax /mo | `=R44/12` |
| T | NET PAY /mo | `=H44+E44+G44-K44-L44-M44-S44` |
| U | Total exempt /yr | `=E44*12+G44*12+F44-P44` |
| W–AB | Baseline comparison | Same math with `A` fixed at `$B$28` — the pre-optimization case |
| AC | **TAX SAVED /yr** | `=AB44-R44` |
| AE | 2316: De minimis /yr | `=E44*12` |
| AF | 2316: 13th mo + benefits (max 90k) | `=MIN(O44,$B$26)` |
| AG | 2316: taxable spill | `=P44` |

**SSS base is `D−E`** (gross less de minimis), not basic. Verify this matches what is
actually reported to SSS — their definition of compensation is not identical to BIR's.

**PhilHealth base is `H`** (basic only) — correctly excludes de minimis, the incentive, and
overtime.

---

## 9. Tax table — `A35:D40`

TRAIN rates, effective 2023 onward. Lookup pattern:

```
tax = INDEX(base, MATCH(x, over, 1)) + (x − INDEX(threshold, MATCH(x, over, 1))) * INDEX(rate, MATCH(x, over, 1))
```

| Over | Base tax | Rate on excess |
|---|---|---|
| 0 | 0 | 0% |
| 250,000 | 0 | 15% |
| 400,000 | 22,500 | 20% |
| 800,000 | 102,500 | 25% |
| 2,000,000 | 402,500 | 30% |
| 8,000,000 | 2,202,500 | 35% |

Uses `INDEX`/`MATCH`, not `VLOOKUP`. Do not convert to `XLOOKUP`/`FILTER`/`SORT` — they do not
survive non-Excel recalculation and produce silent truncation.

---

## 10. Decision rules and invariants

**Who gets restructured (`C` = `Yes`/`No`):**

Set `No` when annual taxable income is already below PHP 250,000 (the zero bracket).
Restructuring gains such an employee nothing in tax while eroding their 13th month base,
SSS accrual, and minimum-wage headroom.

Currently `No`: Farinas, Feliciano, Nacional, Santelices.

**Hard invariants — a change that breaks one of these is a bug:**

1. `D + A + B = G` for every row. Monthly take-home must equal signed gross.
2. `J` must read `OK` on every row. A `BREACH` is a wage violation, not a tax outcome.
3. `F ≥ H` — the 13th-month-date payment must cover the statutory 13th month.
4. Rows marked `No` must have `A = B27 − C19` and must not be optimized. This is the
   **hold-harmless** rule: it pins their taxable basic to `D − B27`, the baseline, so a change to
   the de minimis schedule cannot push them into tax. Verify by confirming their `AC` reads 0.00.
5. Never write into columns E–AG. They are formulas. Inputs are C, D only.

**Non-negotiable compliance requirement:**

The productivity incentive (column G) must carry:
- a **threshold that could genuinely fail** (deliverables accepted, minimum output, no
  unresolved disciplinary action — set where staff normally clear it), and
- a **monthly determination recorded per employee** (criteria met, amount released, approver).

A fixed amount paid unconditionally is regular compensation regardless of the column header.
If reclassified, the PHP 90,000 exclusion is lost on ~PHP 632,700/yr of payments, reversing
the PHP 70,465 saving and adding a 25% surcharge plus 12% annual interest, with the company
liable as withholding agent.

Sizing the incentive off gross salary is **fine** — the 13th month is one month of basic and
nobody disputes its character. Invariance is the defect, not derivation.

Frequency is not the issue either. Monthly incentives are ordinary. **Do not convert to
quarterly for existing staff** — it reduces monthly take-home for eight months of the year and
runs into Art. 100 non-diminution. Quarterly is available for new hires only, where the pattern
is set at signing.

---

## 11. Edge cases

**Garcia (row 53) is saturated.** His 13th month alone (94,700) exceeds the 90,000 ceiling
before any benefit is added. Bucket = 106,700, spill = 16,700, and annual taxable is constant
across every configuration — `A` and spill move in lockstep. `AC53` correctly reads 0.00.
His only remaining levers are outside this model: a non-cash achievement award, or an
RA 4917 retirement plan.

**Nipas (row 57)** clears the ceiling by a thin margin. Any salary increase tips him into
spill. Watch `P57`.

**Dionisio and Ramos-Jones are excluded from rows 44–59.** They are consultants, not
employees — `05_2026` rows 29–30 gross them up at `/0.9` with 10% and 5% columns, which is
professional-fee EWT. In `Sheet8` they had PhilHealth deducted with zero tax withheld, which
fits neither treatment. See §12.

---

## 12. Consultants — rows 68–70

| | Dionisio | Ramos-Jones |
|---|---|---|
| Gross receipts /yr | 1,193,345.45 | 1,193,345.45 |
| 8% option (less 250k) | 75,467.64 | 75,467.64 |
| Graduated + 40% OSD | 85,701.45 | 85,701.45 |
| + 3% percentage tax | 35,800.36 | 35,800.36 |
| **Saving with 8%** | **46,034.18** | **46,034.18** |
| | | **Total 92,068.36** |

Both are under the PHP 3M VAT threshold, so the 8% rate substitutes for **both** graduated
income tax and percentage tax.

**This is worth more than the entire employee restructure and breaks none of the operating
constraints.** It must be elected on the **first quarterly return of the taxable year** —
missing the election locks the graduated regime for twelve months.

---

## 13. Levers not in this model

| Lever | Value /yr | Why excluded |
|---|---|---|
| Consultants → 8% election | 92,068 | In the tab (§12), not yet actioned |
| Leave monetization, 10 days | ~44,001 | Needs its own payment or the 13th-month run |
| RA 4917 retirement plan | largest for high earners | New instrument, employer-funded, BIR-registered |
| Garcia's award as tangible property | ~4,175 | Must be non-cash |

---

## 14. Verification procedure

After any edit, in order:

1. `openpyxl` writes formulas with **no cached values**. Any tool reading cached values sees
   `None` until recalculated.
2. Recalculate through Excel COM (`CalculateFullRebuild`, then `Save`). LibreOffice is not
   installed; the skill's `recalc.py` fails on Windows with `AF_UNIX`.
3. Scan the tab for `#REF!` / `#VALUE!` / `#NAME?` / `######`. Expect **0**.
4. Confirm `AC60` = 70,465.10 and `U44` = 141,600.00 unless a lever was deliberately changed.
5. Confirm `J44:J59` all read `OK`.
6. Confirm `05_2026` still has exactly 456 error cells — more means the edit damaged it.

**Do not edit `sheet_view` selections by hand.** Setting `freeze_panes` from a row+column
freeze to a column-only freeze leaves orphaned `<selection pane="bottomLeft">` and
`bottomRight` elements. The resulting XML is invalid and **Excel silently refuses to open the
workbook**. Correct state is one `<pane xSplit="2">` and exactly one `<selection>`.

---

## 15. Open items

1. **Verify `B29` / `B30`** — minimum wage daily rate and working-day divisor are placeholders.
2. **Write the productivity incentive scheme document** — metric, threshold, formula, approver,
   explicit statement that it is not part of basic salary and not guaranteed. Without it,
   column G is a renamed salary line.
3. **Add the monthly determination step** to the payroll process.
4. **File the 8% election** for the two consultants.
5. **Confirm the SSS reporting base** matches `D−E`.
6. **Confirm the carve-out is reflected in employment contracts.** If contracts state a single
   gross figure and the split exists only in payroll, the payroll register is the primary
   record on examination and that is the exposure. This was raised and accepted by the client.
7. **Set up the medicine substantiation process.** Item 17 is now paid as monthly cash, which is
   only defensible with evidence on file. Collect receipts or a signed declaration covering the
   PHP 10,000 each December. Without it the item is a renamed salary line.
8. **Christmas gift — accepted risk, revisit annually.** Paid as monthly cash by client decision
   against advice; see §5. ~PHP 10,800/yr exposure. The fix costs nothing but timing: move it to a
   single PHP 5,000 payment on the December 13th-month date.
9. **Derived entitlements were not held constant.** Total cash is preserved, but every peso
   moved out of basic reduces overtime and night-differential rates, SSS and PhilHealth
   benefit accrual, separation pay, and retirement pay.
