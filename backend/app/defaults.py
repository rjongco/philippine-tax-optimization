"""Seed scenario — the state of COMPUTATIONS.xlsx as last verified (2026-08-05).

These values are the golden test's expectations. Changing anything here changes what
the app considers correct, so change it only alongside the workbook.
"""

from .engine.models import DeMinimisItem, Employee, Parameters, Scenario
from .engine.money import dec


def default_parameters() -> Parameters:
    return Parameters()


def default_deminimis() -> list[DeMinimisItem]:
    """Tier 1 schedule at RR 29-2025 ceilings. Seven items, total 6,399.99/mo.

    RR 29-2025 was issued 22 December 2025 and took effect 6 January 2026,
    raising every ceiling on the list and — materially for this model — allowing
    employee achievement awards to be paid in CASH for the first time.

    Monthly figures round DOWN where an annual cap does not divide evenly
    (uniform 8,000/12, medical dependents 4,000/12), so no line sits above its
    statutory ceiling. That is why the total is 6,399.99 rather than a round
    6,400.00: granting above a cap is strictly worse than not granting at all,
    because the excess drops into the already-full 90,000 bucket.
    """
    return [
        DeMinimisItem(
            key="rice",
            label="Rice subsidy",
            statutory_cap_monthly=dec("2500"),
            granted_monthly=dec("2500"),
            authority="RR 29-2025 — PHP 2,500/mo (was 2,000)",
            note="Cash is expressly allowed for this item. Monthly cap, so it splits "
            "cleanly across pay cutoffs.",
        ),
        DeMinimisItem(
            key="uniform",
            label="Uniform and clothing allowance",
            statutory_cap_monthly=dec("666.66"),
            granted_monthly=dec("666.66"),
            authority="RR 29-2025 — PHP 8,000/yr (was 6,000, then 7,000 under RR 4-2025)",
            note="Annual cap amortised monthly, rounded down so the annual total "
            "(7,999.92) stays under the 8,000 ceiling. This line moved twice in one "
            "year — check it against the current regulation before relying on it.",
        ),
        DeMinimisItem(
            key="laundry",
            label="Laundry allowance",
            statutory_cap_monthly=dec("400"),
            granted_monthly=dec("400"),
            authority="RR 29-2025 — PHP 400/mo (was 300)",
            note="Monthly cap. Splits cleanly.",
        ),
        DeMinimisItem(
            key="medical_dependents",
            label="Medical cash allowance — dependents",
            statutory_cap_monthly=dec("333.33"),
            granted_monthly=dec("333.33"),
            authority="RR 29-2025 — PHP 2,000 per semester, or PHP 333/mo (was 1,500)",
            note="The regulation states the monthly equivalent itself, and says "
            "'cash' expressly. The strongest item on the schedule.",
        ),
        DeMinimisItem(
            key="medicine",
            label="Medicine / maintenance assistance",
            statutory_cap_monthly=dec("1000"),
            granted_monthly=dec("1000"),
            authority="RR 29-2025 — actual medical assistance, PHP 12,000/yr (was 10,000)",
            note="Paid as scheduled monthly cash, which is defensible ONLY with annual "
            "substantiation on file (receipts or a signed declaration covering the "
            "PHP 12,000). The regulation's word is 'actual' — an evidentiary test, not "
            "a timing test, so payment need not match expense timing. Without "
            "substantiation this falls out of Tier 1 into the 90,000 ceiling, which is "
            "already full, and becomes fully taxable.",
            unconditional=False,
        ),
        DeMinimisItem(
            key="achievement_award",
            label="Employee achievement award",
            statutory_cap_monthly=dec("1000"),
            granted_monthly=dec("1000"),
            authority="RR 29-2025 — PHP 12,000/yr, cash now permitted (was 10,000, non-cash only)",
            note="NEW under RR 29-2025, and the single biggest change for this model. "
            "The regulation now reads 'in any form, whether in cash, gift certificate, "
            "or any tangible personal property'. Cash was previously disqualifying, "
            "which is why this item was excluded before. PRECONDITION: it must be paid "
            "'under an established written plan which does not discriminate in favor of "
            "highly paid employees'. That plan must exist before this line is paid — "
            "without it the item is not a de minimis benefit at all. Note the conditions "
            "are weaker than the 90,000 bucket demands: no requirement that it be "
            "capable of failing.",
            unconditional=False,
        ),
        DeMinimisItem(
            key="christmas",
            label="Christmas gift",
            statutory_cap_monthly=dec("500"),
            granted_monthly=dec("500"),
            authority="RR 29-2025 — gifts during Christmas and major anniversaries, PHP 6,000/yr (was 5,000)",
            note="WEAKEST ITEM ON THE SCHEDULE — retained by client decision. The higher "
            "ceiling changes nothing about the two defects, and unlike the medicine item "
            "no substantiation cures either: (1) a gift is gratuitous by definition, and "
            "this one is carved out of contracted gross, so the employee was entitled to "
            "the money regardless; (2) the regulation says gifts given during CHRISTMAS — "
            "an occasion test that monthly release does not meet. The achievement award "
            "above is now the stronger home for this money: same cash, explicitly "
            "permitted, no occasion requirement.",
            unconditional=False,
        ),
    ]


def default_employees() -> list[Employee]:
    """The 16 employees on rows 44-59 of the workbook.

    Consultants (Dionisio, Ramos-Jones) are deliberately absent: they are not
    employees, and their 8% gross receipts election is a separate calculation.
    """
    raw = [
        ("avila", "Avila, Jean Madeleine T.", "50000", True),
        ("banguilan", "Banguilan, Melborne T.", "33000", True),
        ("carpo", "Carpo, Alexander Morris R.", "40000", True),
        ("cruz", "Cruz, Raziele Divine N.", "35000", True),
        ("deleon", "De Leon, Michael G.", "39554", True),
        ("defeo", "Defeo, Rolando Jr.", "40000", True),
        ("delrosario", "Del Rosario, Roberto Matrin", "50000", True),
        ("farinas", "Farinas, Cherry Lou T.", "25000", False),
        ("feliciano", "Feliciano, Jan Marion", "27000", False),
        ("garcia", "Garcia, Robin Michael U.", "100000", True),
        ("garciano", "Garciano, Fil III B.", "50000", True),
        ("ismael", "Ismael, Nadine Janica", "38000", True),
        ("nacional", "Nacional, Krystan Gene H.", "28000", False),
        ("nipas", "Nipas, Lezel A.", "60000", True),
        ("sampiano", "Sampiano, Kyle Therese", "40000", True),
        ("santelices", "Santelices, Maissy A.", "27000", False),
    ]
    return [
        Employee(
            id=i, name=n, signed_gross_monthly=dec(g), restructure=r
        )
        for i, n, g, r in raw
    ]


def default_scenario() -> Scenario:
    return Scenario(
        parameters=default_parameters(),
        deminimis_items=default_deminimis(),
        employees=default_employees(),
    )
