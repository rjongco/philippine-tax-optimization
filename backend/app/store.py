"""Persistence — a single scenario in a single JSON file.

One company, sixteen employees, no history. A database would be ceremony. Decimals
are stored as strings so a save/load round trip cannot lose precision through JSON's
float representation.

This module knows nothing about the model; it reads and writes.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from .defaults import default_scenario
from .engine.models import DeMinimisItem, Employee, Parameters, Scenario
from .engine.money import dec

DATA_DIR = Path(os.environ.get("PAYROLL_DATA_DIR", Path(__file__).parent.parent / "data"))
SCENARIO_PATH = DATA_DIR / "scenario.json"

_PARAM_FIELDS = (
    "philhealth_rate", "philhealth_floor", "philhealth_ceiling", "pagibig_employee",
    "benefits_ceiling", "cash_anchor", "baseline_award", "min_wage_daily",
    "working_days",
)


def _serialize(scenario: Scenario) -> Dict[str, Any]:
    p = scenario.parameters
    return {
        "parameters": {f: str(getattr(p, f)) for f in _PARAM_FIELDS},
        "deminimis_items": [
            {
                "key": i.key,
                "label": i.label,
                "statutory_cap_monthly": str(i.statutory_cap_monthly),
                "granted_monthly": str(i.granted_monthly),
                "authority": i.authority,
                "note": i.note,
                "unconditional": i.unconditional,
            }
            for i in scenario.deminimis_items
        ],
        "employees": [
            {
                "id": e.id,
                "name": e.name,
                "signed_gross_monthly": str(e.signed_gross_monthly),
                "restructure": e.restructure,
            }
            for e in scenario.employees
        ],
    }


def _deserialize(raw: Dict[str, Any]) -> Scenario:
    return Scenario(
        parameters=Parameters(
            **{f: dec(raw["parameters"][f]) for f in _PARAM_FIELDS}
        ),
        deminimis_items=[
            DeMinimisItem(
                key=i["key"],
                label=i["label"],
                statutory_cap_monthly=dec(i["statutory_cap_monthly"]),
                granted_monthly=dec(i["granted_monthly"]),
                authority=i.get("authority", ""),
                note=i.get("note", ""),
                unconditional=i.get("unconditional", True),
            )
            for i in raw["deminimis_items"]
        ],
        employees=[
            Employee(
                id=e["id"],
                name=e["name"],
                signed_gross_monthly=dec(e["signed_gross_monthly"]),
                restructure=e["restructure"],
            )
            for e in raw["employees"]
        ],
    )


def load() -> Scenario:
    """Current scenario, seeding from defaults on first run."""
    if not SCENARIO_PATH.exists():
        scenario = default_scenario()
        save(scenario)
        return scenario
    raw = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    return _deserialize(raw)


def save(scenario: Scenario) -> None:
    """Write atomically — a crash mid-write must not leave a truncated file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(_serialize(scenario), indent=2)
    fd, tmp = tempfile.mkstemp(dir=DATA_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
        os.replace(tmp, SCENARIO_PATH)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def reset() -> Scenario:
    """Back to the seeded workbook values."""
    scenario = default_scenario()
    save(scenario)
    return scenario
