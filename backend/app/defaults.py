"""Seed scenario — the state of COMPUTATIONS.xlsx as last verified (2026-08-05).

These values are the golden test's expectations. Changing anything here changes what
the app considers correct, so change it only alongside the workbook.
"""

from .engine.models import DeMinimisItem, Employee, Parameters, Scenario
from .engine.money import dec


def default_parameters() -> Parameters:
    return Parameters()


def default_deminimis() -> list[DeMinimisItem]:
    """Tier 1 schedule, all six items at statutory cap. Total 4,300.00/mo."""
    return [
        DeMinimisItem(
            key="rice",
            label="Rice subsidy",
            statutory_cap_monthly=dec("2000"),
            granted_monthly=dec("2000"),
            authority="RR 11-2018 — PHP 2,000/mo",
            note="Cash is expressly allowed for this item. Monthly cap, so it splits "
            "cleanly across pay cutoffs.",
        ),
        DeMinimisItem(
            key="uniform",
            label="Uniform and clothing allowance",
            statutory_cap_monthly=dec("500"),
            granted_monthly=dec("500"),
            authority="RR 5-2011 — PHP 6,000/yr",
            note="Annual cap amortised monthly. Staying under the annual total keeps "
            "this within Tier 1.",
        ),
        DeMinimisItem(
            key="laundry",
            label="Laundry allowance",
            statutory_cap_monthly=dec("300"),
            granted_monthly=dec("300"),
            authority="RR 5-2011 — PHP 300/mo",
            note="Monthly cap. Splits cleanly.",
        ),
        DeMinimisItem(
            key="medical_dependents",
            label="Medical cash allowance — dependents",
            statutory_cap_monthly=dec("250"),
            granted_monthly=dec("250"),
            authority="RR 5-2011 — PHP 1,500 per semester, or PHP 250/mo",
            note="The regulation states the monthly equivalent itself, and says "
            "'cash' expressly. The strongest item on the schedule.",
        ),
        DeMinimisItem(
            key="medicine",
            label="Medicine / maintenance assistance",
            statutory_cap_monthly=dec("833.33"),
            granted_monthly=dec("833.33"),
            authority="RR 5-2011 — actual medical assistance, PHP 10,000/yr",
            note="Paid as scheduled monthly cash, which is defensible ONLY with annual "
            "substantiation on file (receipts or a signed declaration covering the "
            "PHP 10,000). The regulation's word is 'actual' — an evidentiary test, not "
            "a timing test, so payment need not match expense timing. Without "
            "substantiation this falls out of Tier 1 into the 90,000 ceiling, which is "
            "already full, and becomes fully taxable.",
            unconditional=False,
        ),
        DeMinimisItem(
            key="christmas",
            label="Christmas gift",
            statutory_cap_monthly=dec("416.67"),
            granted_monthly=dec("416.67"),
            authority="RR 5-2011 — gifts given during Christmas, PHP 5,000/yr",
            note="WEAKEST ITEM ON THE SCHEDULE — retained by client decision. Two "
            "defects, and unlike the medicine item no substantiation cures either: "
            "(1) a gift is gratuitous by definition, and this one is carved out of "
            "contracted gross, so the employee was entitled to the money regardless; "
            "(2) the regulation says gifts given during CHRISTMAS — an occasion test "
            "that monthly release does not meet. Exposure if reclassified is roughly "
            "PHP 10,800/yr across the group. The compliant alternative is a single "
            "PHP 5,000 payment on the existing December 13th-month date, costing "
            "PHP 416.67/mo in monthly cash.",
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
