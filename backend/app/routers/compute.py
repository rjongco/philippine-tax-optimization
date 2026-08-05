"""Computation and payout schedule.

Both endpoints are stateless: they take the scenario in the request body rather than
reading storage, so the UI can preview unsaved edits without committing them.
"""

from typing import List

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..engine import compute as run_compute
from ..engine.schedule import build_schedules
from ..export import build_workbook, export_filename
from ..schemas import ResultOut, ScenarioIn, ScheduleOut

router = APIRouter(prefix="/api", tags=["compute"])

XLSX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


@router.post("/compute", response_model=ResultOut)
def post_compute(payload: ScenarioIn) -> ResultOut:
    return ResultOut.of(run_compute(payload.to_engine()))


@router.post("/schedule", response_model=List[ScheduleOut])
def post_schedule(payload: ScenarioIn) -> List[ScheduleOut]:
    scenario = payload.to_engine()
    result = run_compute(scenario)
    schedules = build_schedules(result.breakdowns, scenario.parameters)
    return [ScheduleOut.of(s) for s in schedules]


@router.post("/export/xlsx")
def post_export_xlsx(payload: ScenarioIn) -> StreamingResponse:
    """The breakdown as a live Excel workbook.

    Carries formulas rather than baked values, so the recipient can change a salary
    and watch the sheet recalculate. See app/export.py for why, and
    tests/test_export.py for the guard against the two implementations drifting.
    """
    scenario = payload.to_engine()
    result = run_compute(scenario)
    buffer = build_workbook(scenario, result)
    filename = export_filename()

    return StreamingResponse(
        buffer,
        media_type=XLSX_MEDIA_TYPE,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            # The browser cannot read Content-Disposition cross-origin without this.
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
