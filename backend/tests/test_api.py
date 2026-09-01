"""API surface, and the precision guarantee across the wire."""

import json
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import SCENARIO_PATH

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_store():
    SCENARIO_PATH.unlink(missing_ok=True)
    yield
    SCENARIO_PATH.unlink(missing_ok=True)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_scenario_seeds_from_defaults_on_first_read():
    body = client.get("/api/scenario").json()
    assert len(body["employees"]) == 16
    assert len(body["deminimis_items"]) == 7
    assert body["deminimis_monthly"] == 6399.99
    assert body["parameters"]["cash_anchor"] == 5300.0


def test_compute_reproduces_the_workbook_total():
    scenario = client.get("/api/scenario").json()
    payload = _to_input(scenario)
    body = client.post("/api/compute", json=payload).json()

    assert len(body["breakdowns"]) == 16
    assert body["totals"]["tax_saved_annual"] == pytest.approx(119507.00, abs=0.01)
    assert body["warnings"] == []

    avila = next(b for b in body["breakdowns"] if b["employee_id"] == "avila")
    assert avila["total_exempt_annual"] == pytest.approx(166799.88, abs=0.01)
    assert avila["invariants"]["all_ok"] is True


def test_saturated_employee_is_flagged_and_explained():
    payload = _to_input(client.get("/api/scenario").json())
    body = client.post("/api/compute", json=payload).json()
    garcia = next(b for b in body["breakdowns"] if b["employee_id"] == "garcia")

    assert garcia["saturated"] is True
    # Saturated, but no longer a dead end: the larger RR 29-2025 de minimis comes
    # out of taxable basic, which his spill does not touch.
    assert garcia["tax_saved_annual"] > 0.0
    assert any("Saturated" in n for n in garcia["notes"])


def test_non_restructured_employees_report_held_harmless():
    payload = _to_input(client.get("/api/scenario").json())
    body = client.post("/api/compute", json=payload).json()

    for b in body["breakdowns"]:
        if not b["restructure"]:
            assert b["invariants"]["held_harmless"] is True, b["name"]
            # Never worse off. Better off is allowed — the hold-harmless clamp
            # binds now that de minimis exceeds the cash anchor.
            assert b["tax_saved_annual"] >= 0.0, b["name"]
            assert b["incentive_monthly"] >= 0.0, b["name"]


def test_editing_a_salary_recomputes():
    scenario = client.get("/api/scenario").json()
    payload = _to_input(scenario)
    payload["employees"][0]["signed_gross_monthly"] = "60000"

    body = client.post("/api/compute", json=payload).json()
    avila = next(b for b in body["breakdowns"] if b["employee_id"] == "avila")
    assert avila["signed_gross_monthly"] == 60000.0
    assert avila["total_exempt_annual"] == pytest.approx(166799.88, abs=0.01)


def test_put_scenario_round_trips_without_losing_precision():
    scenario = client.get("/api/scenario").json()
    payload = _to_input(scenario)
    client.put("/api/scenario", json=payload)

    stored = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    uniform = next(
        i for i in stored["deminimis_items"] if i["key"] == "uniform"
    )
    # stored as a string, so 666.66 survives rather than becoming 666.6599999...
    assert uniform["granted_monthly"] == "666.66"
    assert Decimal(uniform["granted_monthly"]) == Decimal("666.66")

    reread = client.get("/api/scenario").json()
    assert reread["deminimis_monthly"] == 6399.99


def test_over_cap_deminimis_produces_a_warning():
    payload = _to_input(client.get("/api/scenario").json())
    payload["deminimis_items"][0]["granted_monthly"] = "5000"  # rice, cap 2,000

    body = client.post("/api/compute", json=payload).json()
    assert any("Rice subsidy" in w for w in body["warnings"])


def test_minimum_wage_breach_is_reported():
    payload = _to_input(client.get("/api/scenario").json())
    payload["parameters"]["min_wage_daily"] = "2000"  # far above every daily rate

    body = client.post("/api/compute", json=payload).json()
    assert any("Minimum wage breach" in w for w in body["warnings"])
    assert any(not b["invariants"]["minimum_wage_ok"] for b in body["breakdowns"])


def test_parameter_docs_cover_every_editable_parameter():
    docs = client.get("/api/parameters/meta").json()
    scenario = client.get("/api/scenario").json()

    documented = {d["key"] for d in docs}
    configurable = set(scenario["parameters"]) - {"minimum_basic_monthly"}
    assert configurable == documented

    for d in docs:
        assert d["category"] in {"fact", "lever", "assumption"}
        assert d["description"] and d["affects"] and d["authority"]

    assumptions = {d["key"] for d in docs if d["category"] == "assumption"}
    assert assumptions == {"min_wage_daily", "working_days"}
    for d in docs:
        if d["category"] == "assumption":
            assert d["warning"] and "PLACEHOLDER" in d["warning"]


def test_schedule_endpoint_returns_reconciling_schedules():
    payload = _to_input(client.get("/api/scenario").json())
    body = client.post("/api/schedule", json=payload).json()

    assert len(body) == 16
    for s in body:
        assert s["reconciles"] is True, s["name"]
        assert len(s["cutoffs"]) == 24
        assert len(s["months"]) == 12

    avila = next(s for s in body if s["employee_id"] == "avila")
    december = [c for c in avila["cutoffs"] if c["month"] == 12]
    assert december[0]["thirteenth_month"] > 0
    assert december[1]["thirteenth_month"] == 0


def test_reset_restores_seeded_values():
    payload = _to_input(client.get("/api/scenario").json())
    payload["employees"][0]["signed_gross_monthly"] = "999999"
    client.put("/api/scenario", json=payload)
    assert client.get("/api/scenario").json()["employees"][0][
        "signed_gross_monthly"
    ] == 999999.0

    body = client.post("/api/scenario/reset").json()
    assert body["employees"][0]["signed_gross_monthly"] == 50000.0


def _to_input(scenario_out: dict) -> dict:
    """ScenarioOut carries derived fields the input model does not accept."""
    params = {
        k: str(v)
        for k, v in scenario_out["parameters"].items()
        if k != "minimum_basic_monthly"
    }
    return {
        "parameters": params,
        "deminimis_items": [
            {
                "key": i["key"],
                "label": i["label"],
                "statutory_cap_monthly": str(i["statutory_cap_monthly"]),
                "granted_monthly": str(i["granted_monthly"]),
                "authority": i["authority"],
                "note": i["note"],
                "unconditional": i["unconditional"],
            }
            for i in scenario_out["deminimis_items"]
        ],
        "employees": [
            {
                "id": e["id"],
                "name": e["name"],
                "signed_gross_monthly": str(e["signed_gross_monthly"]),
                "restructure": e["restructure"],
            }
            for e in scenario_out["employees"]
        ],
    }
