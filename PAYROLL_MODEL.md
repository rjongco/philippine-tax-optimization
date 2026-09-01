# Payroll Tax Optimization Model — AI Context Reference

**Subject file:** `COMPUTATIONS.xlsx`
**Primary tab:** `Optimized Structure`
**Jurisdiction:** Philippines (BIR / DOLE / SSS / PhilHealth / Pag-IBIG)
**Last verified:** 2026-08-06 — **RR 29-2025 ceilings applied.** Excel full rebuild,
0 error cells, `AC61` = 119,507.00

> **Row numbers moved.** Inserting the achievement-award line pushed everything below
> row 18 down by one. The employee table now starts at row 45, not 44. Any script or
> note written against the old layout is stale.

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

**Result:** every restructured employee reaches exactly **PHP 166,799.88/year exempt**
(= 76,799.88 de minimis + 90,000 benefits ceiling). This is the mathematical ceiling under
Philippine law. It cannot be exceeded without paying additional money.

**Measured effect:** PHP 119,507.00/year total tax saved across 16 employees, at zero
incremental company cost.

Both figures rose sharply under **RR 29-2025** (issued 22 December 2025, effective
6 January 2026), which raised every de minimis ceiling and, decisively, allowed employee
achievement awards to be paid in **cash** for the first time. Before it: 141,600 exempt
and 70,465.10 saved.

---

## 2. Core concept — the two exemption tiers

This is the single most important thing to understand. Conflating these tiers produces
wrong answers.

| | **Tier 1 — De minimis** | **Tier 2 — 13th month & other benefits** |
|---|---|---|
| Authority | RR 5-2011, as last amended by **RR 29-2025** | NIRC Sec. 32(B)(7)(e) |
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
| 11–20 | §1 De minimis schedule, seven items. **Total at `C20`** |
| 22–32 | §2 Parameters. **All model levers live here** |
| 34–41 | §3 TRAIN annual tax table. Lookup range `A36:D41` |
| 43–61 | §4 Employee computation. Header row 44, data **rows 45–60**, total row 61 |
| 62–65 | Notes on the 2316 mapping and exclusions |
| 67–73 | §5 Consultants — 8% gross receipts election |
| 75–84 | §6 Operating caveats |

Freeze pane is `C1` — **columns only, zero frozen rows**. Do not set a row freeze; an earlier
row+column freeze made the sheet unscrollable.

**Inserting rows into the de minimis block must be done through Excel, not openpyxl.**
openpyxl's `insert_rows` does not translate formulas: every `$C$19` elsewhere on the sheet
would keep pointing at row 19 after the total moved to row 20, silently reading a de minimis
line instead of the total. Excel's own `Rows.Insert` retranslates every reference. Insert
*inside* the summed range (at the last item, not at the total row) so `SUM(C13:C18)` expands
rather than leaving the new row out.

---

## 5. De minimis schedule (Tier 1) — rows 13–20

Ceilings per **RR 29-2025**, issued 22 December 2025, effective 6 January 2026. All seven
items at statutory cap. Total `C20` = **6,399.99/month = 76,799.88/year**.

| Row | Item | /mo | /yr | Was | Condition |
|---|---|---|---|---|---|
| 13 | Rice subsidy | 2,500.00 | 30,000 | 2,000/mo | Cash expressly allowed |
| 14 | Uniform and clothing | 666.66 | 7,999.92 | 6,000/yr | Rounded down, see below |
| 15 | Laundry | 400.00 | 4,800 | 300/mo | — |
| 16 | Medical cash allowance, dependents | 333.33 | 3,999.96 | 1,500/sem | PHP 2,000/semester |
| 17 | Medicine / maintenance | 1,000.00 | 12,000 | 10,000/yr | **Monthly cash + annual substantiation** |
| 18 | **Employee achievement award** | 1,000.00 | 12,000 | *excluded* | **Cash now permitted — needs a written plan** |
| 19 | Christmas gift | 500.00 | 6,000 | 5,000/yr | **Monthly cash — weakest item, see below** |
| **20** | **TOTAL** | **6,399.99** | **76,799.88** | 4,300.00 | |

**Why 6,399.99 and not 6,400.00.** Uniform (8,000/12) and medical-dependents (4,000/12) do
not divide evenly. Both round **down**, because granting above a cap is strictly worse than
not granting at all — the excess drops into the already-full 90,000 bucket and is taxed while
still costing the company. One centavo of tidiness is not worth that.

**Item 18 is new, and it is the biggest change in this revision.** RR 29-2025 rewrote the
achievement award to read *"in any form, whether in **cash**, gift certificate, or any
tangible personal property"*. Cash was previously disqualifying, which is why earlier versions
of this document excluded the item outright. **Precondition:** it must be paid *"under an
established written plan which does not discriminate in favor of highly paid employees."*
Without that plan on file it is not a de minimis benefit at all. Note the conditions are
*weaker* than Tier 2 demands — nothing requires the award to be capable of failing.

**Still excluded — do not add back without checking the condition:**

- **CBA / productivity incentive de minimis (now PHP 12,000/yr).** Requires an actual CBA or a
  productivity scheme **registered under RA 6971** with DOLE/NWPC. Worth taking: registering
  the existing incentive scheme would land 12,000/yr in Tier 1 *and* strengthen the
  Sec. 32(B)(7)(e) characterisation of the monthly incentive, which is the model's weakest
  joint. One document, two problems.
- **Leave monetization (now max 12 days, was 10).** Legitimate Tier 1 item that does **not**
  consume the 90k. Excluded only because paying it requires either its own date or the
  13th-month run. Worth ~PHP 52,800/yr if activated. Requires a written VL policy and actual
  unused credits.
- **OT / night-shift meal allowance (now 30% of the regional minimum wage, was 25%).** Per
  day, on actual OT or night-shift days only. Not a flat monthly entitlement.

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

## 6. Parameters — `B23:B32`

| Cell | Parameter | Value | Type |
|---|---|---|---|
| `B23` | PhilHealth employee rate | 0.025 | fact (5% shared equally) |
| `B24` | PhilHealth salary floor | 10,000 | fact |
| `B25` | PhilHealth salary ceiling | 100,000 | fact |
| `B26` | Pag-IBIG employee share | 200 | fact (2% of 10,000 ceiling) |
| `B27` | Benefits exclusion ceiling | 90,000 | fact (NIRC 32(B)(7)(e)) |
| `B28` | Cash anchor — carve-out /mo | 5,300 | **model lever** |
| `B29` | Award — baseline comparison only | 1,000 | **not read by the live model** |
| `B30` | Minimum wage, daily | 695 | **ASSUMPTION — VERIFY** |
| `B31` | Working days divisor | 261 | **ASSUMPTION — VERIFY** |
| `B32` | Minimum basic /mo (floor) | 15,116.25 | `=B30*B31/12` |

**`B28` (cash anchor) is the most consequential cell.** It sets the 13th-month-date payment
via `F = G − B28`, which fixes total annual cash. Changing it changes every employee's total
compensation. It is currently set to preserve the prior structure's cash exactly.

**`B28` also defines hold-harmless.** Employees marked `No` receive `A = MAX(0, B28 − C20)`.
While `C20 ≤ B28` that forces `E + G = B28` and therefore `H = D − B28`, exactly the baseline.

**The clamp is now load-bearing.** Under RR 29-2025 de minimis (6,399.99) *exceeds* the cash
anchor (5,300), so the unclamped expression returns **−1,099.99**. That still pins basic to the
baseline arithmetically, but a negative pay line is nonsense and exports as a negative column
on the payroll register. Clamped at zero, these employees land *below* the old baseline — better
off, never worse — so their tax saving is now `≥ 0` rather than exactly `0`. Do not "fix" a
positive saving on a `No` row; it is correct.

`B28` = 5,300 originally because it equalled de minimis 4,300 + award 1,000. That coincidence
is doubly dead: the model no longer relies on it, and the de minimis side has since outgrown it.
Consider whether 5,300 is still the right anchor now that it no longer covers Tier 1.

**`B29` is baseline-only.** It feeds columns W–AB (the "before" case) and nothing else. It was
formerly hardcoded into column G's `No` branch, which silently taxed the four `No` employees the
moment the de minimis schedule changed. Do not reintroduce it into column G.

**`B30`/`B31` are placeholders.** 695/day at a 261-day (5-day week) divisor. Verify against
the wage order in force and the actual working-day divisor. Use 313 for a 6-day week. These
two cells drive the floor that prevents the optimizer pushing anyone below minimum wage.

---

## 7. The optimization algebra

Notation: `G` signed monthly gross, `D` de minimis, `P` 13th-month-date payment,
`A` productivity incentive, `B` taxable basic, `C` = ceiling (90,000).

```
D = 6,399.99                    (constant, Tier 1 at cap — RR 29-2025)
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
restructured:      A = MIN( MAX( G−D−P , (C−P)/12 , 0 ) , MAX( 0 , G−D−floor ) )
not restructured:  A = MAX( 0 , anchor − D )                     hold-harmless, clamped
```

Constraint (ii) is the binding one for high earners; (i) for everyone else; (iii) is a safety
stop that has not yet bound for any current employee.

**Why every restructured employee lands on 166,799.88:**

```
exempt = 12D + MIN(bucket, C)
       = 76,799.88 + 90,000
       = 166,799.88
```

This holds whether the bucket lands exactly on 90,000 (constraint i binding) or overshoots
(Garcia — the excess becomes spill and is taxed, so capped exempt is still 90,000).

---

## 8. Column reference — row 45 is the template

Every row 45–60 is identical in form. Absolute refs point at parameters; relative refs at the row.

| Col | Header | Formula |
|---|---|---|
| C | Restr? | input `Yes`/`No` |
| D | Signed gross /mo | input |
| E | De minimis /mo | `=$C$20` |
| F | 13th-mo date pay | `=D45-$B$28` |
| G | **Productivity incentive /mo** | `=IF(C45="No",MAX(0,$B$28-$C$20),MIN(MAX(D45-E45-F45,($B$27-F45)/12,0),MAX(0,D45-E45-$B$32)))` |
| H | Taxable basic /mo | `=D45-E45-G45` |
| I | Daily rate | `=H45*12/$B$31` |
| J | Min wage | `=IF(I45>=$B$30,"OK","BREACH")` |
| K | SSS EE | `=INDEX(Sheet9!$L$6:$L$66,MATCH(D45-E45,Sheet9!$A$6:$A$66,1))` |
| L | PhilHealth EE | `=MIN(MAX(H45,$B$24),$B$25)*$B$23` |
| M | Pag-IBIG EE | `=$B$26` |
| N | Net taxable /mo | `=H45-K45-L45-M45` |
| O | Bucket /yr | `=G45*12+F45` |
| P | Spill /yr | `=MAX(0,O45-$B$27)` |
| Q | Annual taxable | `=N45*12+P45` |
| R | Annual tax | `INDEX/MATCH` over `A36:D41` — see §9 |
| S | W/tax /mo | `=R45/12` |
| T | NET PAY /mo | `=H45+E45+G45-K45-L45-M45-S45` |
| U | Total exempt /yr | `=E45*12+G45*12+F45-P45` |
| W | Base basic /mo | `=D45-$B$28` |
| X | Base PHIC | `=MIN(MAX(W45,$B$24),$B$25)*$B$23` |
| Y | Base bucket | `=W45+$B$29*12` |
| Z | Base spill | `=MAX(0,Y45-$B$27)` |
| AA | Base ann taxable | `=(W45-K45-X45-M45)*12+Z45` |
| AB | Base annual tax | `INDEX/MATCH` over `A36:D41` |
| AC | **TAX SAVED /yr** | `=AB45-R45` |
| AE | 2316: De minimis /yr | `=E45*12` |
| AF | 2316: 13th mo + benefits (max 90k) | `=MIN(O45,$B$27)` |
| AG | 2316: taxable spill | `=P45` |

**SSS base is `D−E`** (gross less de minimis), not basic. Verify this matches what is
actually reported to SSS — their definition of compensation is not identical to BIR's.

**PhilHealth base is `H`** (basic only) — correctly excludes de minimis, the incentive, and
overtime.

---

## 9. Tax table — `A36:D41`

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
4. Rows marked `No` must have `A = MAX(0, B28 − C20)` and must not be optimized. This is the
   **hold-harmless** rule: while de minimis stays under the anchor it pins their taxable basic
   to `D − B28`, the baseline. Once de minimis exceeds the anchor — as it does under
   RR 29-2025 — the clamp binds and they land *below* the baseline. Verify by confirming their
   `AC` reads **≥ 0.00**, and that `G` is never negative. A positive saving on a `No` row is
   correct, not a bug.
5. Never write into columns E–AG. They are formulas. Inputs are C, D only.

**Non-negotiable compliance requirement:**

The productivity incentive (column G) must carry:
- a **threshold that could genuinely fail** (deliverables accepted, minimum output, no
  unresolved disciplinary action — set where staff normally clear it), and
- a **monthly determination recorded per employee** (criteria met, amount released, approver).

A fixed amount paid unconditionally is regular compensation regardless of the column header.
If reclassified, the PHP 90,000 exclusion is lost on ~PHP 632,700/yr of payments, reversing
the PHP 119,507 saving and adding a 25% surcharge plus 12% annual interest, with the company
liable as withholding agent.

Sizing the incentive off gross salary is **fine** — the 13th month is one month of basic and
nobody disputes its character. Invariance is the defect, not derivation.

Frequency is not the issue either. Monthly incentives are ordinary. **Do not convert to
quarterly for existing staff** — it reduces monthly take-home for eight months of the year and
runs into Art. 100 non-diminution. Quarterly is available for new hires only, where the pattern
is set at signing.

---

## 11. Edge cases

**Garcia (row 54) is saturated, but no longer a dead end.** His 13th-month payment alone
(94,700) exceeds the 90,000 ceiling before any benefit is added, so his bucket spills however
`A` is set — `A` and spill move in lockstep and his Tier 2 position is fixed. Under the old
schedule that left him at exactly 0.00 saved.

RR 29-2025 changed that. The larger de minimis comes out of **taxable basic**, which the spill
does not touch, so he now saves **6,217.47/yr** with `A` driven to 0 and spill down from 16,700
to 4,700. His remaining levers are still outside this model: an RA 4917 retirement plan, or
raising the cash anchor.

**Nipas (row 58)** clears the ceiling by a thin margin. Any salary increase tips him into
spill. Watch `P58`.

**Dionisio and Ramos-Jones are excluded from rows 45–60.** They are consultants, not
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
| Leave monetization, 12 days | ~52,800 | Needs its own payment or the 13th-month run |
| RA 4917 retirement plan | largest for high earners | New instrument, employer-funded, BIR-registered |
| CBA / productivity de minimis | 12,000/employee | Needs a scheme **registered under RA 6971** with DOLE/NWPC. Best remaining lever: it also strengthens the Sec. 32(B)(7)(e) case for the monthly incentive |

---

## 14. Verification procedure

After any edit, in order:

1. `openpyxl` writes formulas with **no cached values**. Any tool reading cached values sees
   `None` until recalculated.
2. Recalculate through Excel COM (`CalculateFullRebuild`, then `Save`). LibreOffice is not
   installed; the skill's `recalc.py` fails on Windows with `AF_UNIX`.
3. Scan the tab for `#REF!` / `#VALUE!` / `#NAME?` / `######`. Expect **0**.
4. Confirm `AC61` = 119,507.00 and `U45` = 166,799.88 unless a lever was deliberately changed.
5. Confirm `J45:J60` all read `OK`.
6. Confirm `05_2026` still has exactly 456 error cells — more means the edit damaged it.

**Do not edit `sheet_view` selections by hand.** Setting `freeze_panes` from a row+column
freeze to a column-only freeze leaves orphaned `<selection pane="bottomLeft">` and
`bottomRight` elements. The resulting XML is invalid and **Excel silently refuses to open the
workbook**. Correct state is one `<pane xSplit="2">` and exactly one `<selection>`.

---

## 15. Open items

0. **BLOCKING — write the achievement-award plan.** RR 29-2025 requires the award to be paid
   *"under an established written plan which does not discriminate in favor of highly paid
   employees."* The plan must name the qualifying achievements (length of service, safety),
   the amount, and apply across the workforce rather than to senior staff. **The schedule
   already grants 1,000/mo on this line — 12,000/yr per employee — so until the plan exists the
   model is claiming an exemption the company cannot support.** This is the only item here that
   invalidates a live figure rather than merely weakening it.
1. **Verify `B30` / `B31`** — minimum wage daily rate and working-day divisor are placeholders.
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
   PHP 12,000 each December. Without it the item is a renamed salary line.
8. **Christmas gift — accepted risk, revisit annually.** Paid as monthly cash by client decision
   against advice; see §5. The fix costs nothing but timing: move it to a single PHP 6,000
   payment on the December 13th-month date. Now that the achievement award accepts cash with no
   occasion requirement, that line is the better home for this money — reconsider whether the
   Christmas gift is worth carrying at all.
9. **Register the productivity scheme under RA 6971.** Worth 12,000/yr per employee in Tier 1
   (§13) *and* it materially strengthens the Sec. 32(B)(7)(e) characterisation of the monthly
   incentive, which is the model's weakest joint. One document, two problems.
10. **Re-examine the cash anchor.** `B28` = 5,300 was calibrated when it covered the whole
    de minimis schedule plus the award. De minimis is now 6,399.99 and has outgrown it, which
    is why the hold-harmless clamp binds. The model is correct either way, but 5,300 no longer
    means what it was chosen to mean.
11. **Derived entitlements were not held constant.** Total cash is preserved, but every peso
   moved out of basic reduces overtime and night-differential rates, SSS and PhilHealth
   benefit accrual, separation pay, and retirement pay.
